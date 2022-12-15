# Copyright (c) 2018, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json
import os
import requests
import frappe
import mimetypes
from frappe.utils.pdf import cleanup, get_pdf


from frappe import _
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html
from frappe.core.doctype.role.role import get_info_based_on_role, get_user_info
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.integrations.doctype.slack_webhook_url.slack_webhook_url import send_slack_message
from frappe.model.document import Document
from frappe.modules.utils import export_module_json, get_doc_module
from frappe.utils import add_to_date, cast, is_html, nowdate, validate_email_address
from frappe.utils.jinja import validate_template
from frappe.utils.safe_exec import get_safe_globals
from frappe.email.doctype.notification.notification import Notification, get_context, json

class CustomNotification(Notification):
	def onload(self):
		"""load message"""
		if self.is_standard:
			self.message = self.get_template()

	def autoname(self):
		if not self.name:
			self.name = self.subject

	def validate(self):
		if self.channel in ("Email", "Slack", "System Notification"):
			validate_template(self.subject)

		validate_template(self.message)

		if self.event in ("Days Before", "Days After") and not self.date_changed:
			frappe.throw(_("Please specify which date field must be checked"))

		if self.event == "Value Change" and not self.value_changed:
			frappe.throw(_("Please specify which value field must be checked"))

		self.validate_forbidden_types()
		self.validate_condition()
		self.validate_standard()
		frappe.cache().hdel("notifications", self.document_type)
		
	def on_update(self):
		path = export_module_json(self, self.is_standard, self.module)
		if path:
			# js
			if not os.path.exists(path + ".md") and not os.path.exists(path + ".html"):
				with open(path + ".md", "w") as f:
					f.write(self.message)

			# py
			if not os.path.exists(path + ".py"):
				with open(path + ".py", "w") as f:
					f.write(
						"""import frappe

def get_context(context):
	# do your magic here
	pass
"""
					)

	def validate_standard(self):
		if self.is_standard and self.enabled and not frappe.conf.developer_mode:
			frappe.throw(
				_("Cannot edit Standard Notification. To edit, please disable this and duplicate it")
			)

	def validate_condition(self):
		temp_doc = frappe.new_doc(self.document_type)
		if self.condition:
			try:
				frappe.safe_eval(self.condition, None, get_context(temp_doc.as_dict()))
			except Exception:
				frappe.throw(_("The Condition '{0}' is invalid").format(self.condition))

	def validate_forbidden_types(self):
		forbidden_document_types = ("Email Queue",)
		if self.document_type in forbidden_document_types or frappe.get_meta(self.document_type).istable:
			# currently notifications don't work on child tables as events are not fired for each record of child table

			frappe.throw(_("Cannot set Notification on Document Type {0}").format(self.document_type))

	def get_documents_for_today(self):
		"""get list of documents that will be triggered today"""
		docs = []

		diff_days = self.days_in_advance
		if self.event == "Days After":
			diff_days = -diff_days

		reference_date = add_to_date(nowdate(), days=diff_days)
		reference_date_start = reference_date + " 00:00:00.000000"
		reference_date_end = reference_date + " 23:59:59.000000"

		doc_list = frappe.get_all(
			self.document_type,
			fields="name",
			filters=[
				{self.date_changed: (">=", reference_date_start)},
				{self.date_changed: ("<=", reference_date_end)},
			],
		)

		for d in doc_list:
			doc = frappe.get_doc(self.document_type, d.name)

			if self.condition and not frappe.safe_eval(self.condition, None, get_context(doc)):
				continue

			docs.append(doc)

		return docs

	def send(self, doc):
		"""Build recipients and send Notification"""

		context = get_context(doc)
		context = {"doc": doc, "alert": self, "comments": None}
		if doc.get("_comments"):
			context["comments"] = json.loads(doc.get("_comments"))

		if self.is_standard:
			self.load_standard_properties(context)
		try:
			if self.channel == "Email":
				self.send_an_email(doc, context)

			if self.channel == "Slack":
				self.send_a_slack_msg(doc, context)

			if self.channel == "SMS":
				self.send_sms(doc, context)

			if self.channel == "System Notification" or self.send_system_notification:
				self.create_system_notification(doc, context)

			if self.channel == "Whatsapp B2C":
				self.get_api(doc, context)

		except Exception:
			self.log_error("Failed to send Notification")

		if self.set_property_after_alert:
			allow_update = True
			if (
				doc.docstatus.is_submitted()
				and not doc.meta.get_field(self.set_property_after_alert).allow_on_submit
			):
				allow_update = False
			try:
				if allow_update and not doc.flags.in_notification_update:
					fieldname = self.set_property_after_alert
					value = self.property_value
					if doc.meta.get_field(fieldname).fieldtype in frappe.model.numeric_fieldtypes:
						value = frappe.utils.cint(value)

					doc.reload()
					doc.set(fieldname, value)
					doc.flags.updater_reference = {
						"doctype": self.doctype,
						"docname": self.name,
						"label": _("via Notification"),
					}
					doc.flags.in_notification_update = True
					doc.save(ignore_permissions=True)
					doc.flags.in_notification_update = False
			except Exception:
				self.log_error("Document update failed")

	def create_system_notification(self, doc, context):
		subject = self.subject
		if "{" in subject:
			subject = frappe.render_template(self.subject, context)

		attachments = self.get_attachment(doc)

		recipients, cc, bcc = self.get_list_of_recipients(doc, context)

		users = recipients + cc + bcc

		if not users:
			return

		notification_doc = {
			"type": "Alert",
			"document_type": doc.doctype,
			"document_name": doc.name,
			"subject": subject,
			"from_user": doc.modified_by or doc.owner,
			"email_content": frappe.render_template(self.message, context),
			"attached_file": attachments and json.dumps(attachments[0]),
		}
		enqueue_create_notification(users, notification_doc)

	def send_an_email(self, doc, context):
		from email.utils import formataddr

		from frappe.core.doctype.communication.email import _make as make_communication

		subject = self.subject
		if "{" in subject:
			subject = frappe.render_template(self.subject, context)

		attachments = self.get_attachment(doc)
		recipients, cc, bcc = self.get_list_of_recipients(doc, context)
		if not (recipients or cc or bcc):
			return

		sender = None
		message = frappe.render_template(self.message, context)
		if self.sender and self.sender_email:
			sender = formataddr((self.sender, self.sender_email))
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			sender=sender,
			cc=cc,
			bcc=bcc,
			message=message,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
			attachments=attachments,
			expose_recipients="header",
			print_letterhead=((attachments and attachments[0].get("print_letterhead")) or False),
		)

		# Add mail notification to communication list
		# No need to add if it is already a communication.
		if doc.doctype != "Communication":
			make_communication(
				doctype=doc.doctype,
				name=doc.name,
				content=message,
				subject=subject,
				sender=sender,
				recipients=recipients,
				communication_medium="Email",
				send_email=False,
				attachments=attachments,
				cc=cc,
				bcc=bcc,
				communication_type="Automated Message",
			)

	def send_a_slack_msg(self, doc, context):
		send_slack_message(
			webhook_url=self.slack_webhook_url,
			message=frappe.render_template(self.message, context),
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	def send_sms(self, doc, context):
		send_sms(
			receiver_list=self.get_receiver_list(doc, context),
			msg=frappe.render_template(self.message, context),
		)

	def get_list_of_recipients(self, doc, context):
		recipients = []
		cc = []
		bcc = []
		for recipient in self.recipients:
			if recipient.condition:
				if not frappe.safe_eval(recipient.condition, None, context):
					continue
			if recipient.receiver_by_document_field:
				fields = recipient.receiver_by_document_field.split(",")
				# fields from child table
				if len(fields) > 1:
					for d in doc.get(fields[1]):
						email_id = d.get(fields[0])
						if validate_email_address(email_id):
							recipients.append(email_id)
				# field from parent doc
				else:
					email_ids_value = doc.get(fields[0])
					if validate_email_address(email_ids_value):
						email_ids = email_ids_value.replace(",", "\n")
						recipients = recipients + email_ids.split("\n")

			if recipient.cc and "{" in recipient.cc:
				recipient.cc = frappe.render_template(recipient.cc, context)

			if recipient.cc:
				recipient.cc = recipient.cc.replace(",", "\n")
				cc = cc + recipient.cc.split("\n")

			if recipient.bcc and "{" in recipient.bcc:
				recipient.bcc = frappe.render_template(recipient.bcc, context)

			if recipient.bcc:
				recipient.bcc = recipient.bcc.replace(",", "\n")
				bcc = bcc + recipient.bcc.split("\n")

			# For sending emails to specified role
			if recipient.receiver_by_role:
				emails = get_info_based_on_role(recipient.receiver_by_role, "email")

				for email in emails:
					recipients = recipients + email.split("\n")

		if self.send_to_all_assignees:
			recipients = recipients + get_assignees(doc)

		return list(set(recipients)), list(set(cc)), list(set(bcc))

	def get_receiver_list(self, doc, context):
		"""return receiver list based on the doc field and role specified"""
		receiver_list = []
		for recipient in self.recipients:
			if recipient.condition:
				if not frappe.safe_eval(recipient.condition, None, context):
					continue

			# For sending messages to the owner's mobile phone number
			if recipient.receiver_by_document_field == "owner":
				receiver_list += get_user_info([dict(user_name=doc.get("owner"))], "mobile_no")
			# For sending messages to the number specified in the receiver field
			elif recipient.receiver_by_document_field:
				receiver_list.append(doc.get(recipient.receiver_by_document_field))

			# For sending messages to specified role
			if recipient.receiver_by_role:
				receiver_list += get_info_based_on_role(recipient.receiver_by_role, "mobile_no")
		return receiver_list

	def get_attachment(self, doc):
		"""check print settings are attach the pdf"""
		if not self.attach_print:
			return None

		print_settings = frappe.get_doc("Print Settings", "Print Settings")
		if (doc.docstatus == 0 and not print_settings.allow_print_for_draft) or (
			doc.docstatus == 2 and not print_settings.allow_print_for_cancelled
		):

			# ignoring attachment as draft and cancelled documents are not allowed to print
			status = "Draft" if doc.docstatus == 0 else "Cancelled"
			frappe.throw(
				_(
					"""Not allowed to attach {0} document, please enable Allow Print For {0} in Print Settings"""
				).format(status),
				title=_("Error in Notification"),
			)
		else:
			return [
				{
					"print_format_attachment": 1,
					"doctype": doc.doctype,
					"name": doc.name,
					"print_format": self.print_format,
					"print_letterhead": print_settings.with_letterhead,
					"lang": frappe.db.get_value("Print Format", self.print_format, "default_print_language")
					if self.print_format
					else "en",
				}
			]

	def get_template(self):
		module = get_doc_module(self.module, self.doctype, self.name)

		def load_template(extn):
			template = ""
			template_path = os.path.join(os.path.dirname(module.__file__), frappe.scrub(self.name) + extn)
			if os.path.exists(template_path):
				with open(template_path) as f:
					template = f.read()
			return template

		return load_template(".html") or load_template(".md")

	def load_standard_properties(self, context):
		"""load templates and run get_context"""
		module = get_doc_module(self.module, self.doctype, self.name)
		if module:
			if hasattr(module, "get_context"):
				out = module.get_context(context)
				if out:
					context.update(out)

		self.message = self.get_template()

		if not is_html(self.message):
			self.message = frappe.utils.md_to_html(self.message)

	def on_trash(self):
		frappe.cache().hdel("notifications", self.document_type)


	def get_api(self,doc,context):
		wts = frappe.get_doc("Whatsapp Settings")
		
		if wts.enable:
			url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Notification"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
			payload3 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url4, headers=headers, data=payload3)
			c=eval(response.text)
			credit=c.get("data")
			a=flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			
			try:
				if a<flt(wts.current_credits):
    				frappe.throw("Credit Not Enough To Process Api Request")
				if a>flt(wts.current_credits):
					wte=frappe.get_doc("Whatsapp Template",self.whatsapp_template)
					wt = frappe.db.get_all("Notification",{"document_type":wte.doctype_name,"channel":"Whatsapp B2C","enabled":1},["*"])
					params = []
					vb_list = []
					vrb = {}
					types = []
					values = []
					
					mobile_no=self.get_receiver_list(doc, context)
					for m_no in mobile_no:
						if wt:
							wpid = ""
							btoken = ""
							wtemplate = ""
							body = ""
							var = ""

							for i in wt:
								wts = frappe.get_doc("Whatsapp Settings")
								wpid = wts.phone_number_id
								btoken = frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token")
								wtemplate = i.whatsapp_template
								body = wte.body_text

								ct = frappe.db.get_all("WhatsApp Variables",{"parent":wte.name},["*"],order_by='idx')
								
								for k in ct:
									vb_list.append({
										"type": k.field_type,
										"name" : k.field_name
									})

							for i in vb_list:
								if i.get("type") == "Data":
									a=frappe.db.get_value(self.document_type,{"name":doc.name},[i.get("name")])
									i.update({
										"type":"text",
										"text":a
									})
									del i["name"]
								if i.get("type") == "Date":
									a=frappe.db.get_value(self.document_type,{"name":doc.name},[i.get("name")])
									i.update({
										"type":"text",
										"text":a
									})
									del i["name"]
								if i.get("type") == "Link":
									a=frappe.db.get_value(self.document_type,{"name":doc.name},[i.get("name")])
									i.update({
										"type":"text",
										"text":a
									})
									del i["name"]
								
								if i.get("type") == "Currency":                
									i.update({
										"type":"currency",
										"currency":{
											"fallback_value":frappe.db.get_value(self.document_type,{"name":doc.name},[i.get("name")]),
											"code":frappe.db.get_value(self.document_type,{"name":doc.name},["currency"]),
											"amount_1000":1000*flt(frappe.db.get_value(self.document_type,{"name":doc.name},[i.get("name")]))

										}
									})
									del i["name"]
								
								params.append(i)
										
							wts = frappe.get_doc("Whatsapp Settings")         

							url = "https://graph.facebook.com/v15.0/{0}/messages".format(wts.phone_number_id)

							
							
							if wte.header=="Text":
								
								payload1 = json.dumps({
										"recipient_type": "individual",
										"to":m_no,
										"type": "template",
										"messaging_product":"whatsapp",
										"template": {
												"name": wtemplate.lower(),
												"language": {
													"code": "en"
												},
												"components": [{
													"type": "body",
													"parameters": params
												}]
											}
								})
								url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
								payload2 = ""
								headers = {
									'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
									'Content-Type': 'application/json'
									}
								response = requests.request("GET", url2, headers=headers, data=payload2)

								d=eval(response.text)
								a=d.get("data")
								url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Notification"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
								payload3 = ""
								headers = {
									'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
									'Content-Type': 'application/json'
									}
								response = requests.request("GET", url4, headers=headers, data=payload3)
								c=eval(response.text)
								credit=c.get("data")
								doc=frappe.new_doc("Whatsapp Api Call Log")
								doc.api_call="Media Upload"
								doc.opening_credit=wts.current_credits
								doc.credit_in=0
								doc.credit_out=credit.get("credit_consumed")/credit.get("amount_per_credit")
								doc.balance=flt(wts.current_credits)-flt(doc.credit_out)
								doc.save(ignore_permissions=True)
								url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
								payload4 = json.dumps({
									"data": {
										"project":wts.project_hash,
										"app":wts.app_hash,
										"customer":a.get("customer"),
										"api_call":"Notification",
										"api_call_url":url,
										"opening_credit":wts.current_credits,
										"credit_in":0,
										"credit_out":credit.get("credit_consumed")/credit.get("amount_per_credit"),
										"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
										"api_payload":payload1
										}
										})
								headers = {
									'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
									'Content-Type': 'application/json'
									}
								response = requests.request("POST", url3, headers=headers, data=payload4)

							if wte.header=="Media":
								if wte.media_type=="Document":

									html = frappe.get_print(doc, doc.name,print_format=self.print_format, doc=doc , no_letterhead=0)
									report = get_pdf(html)
									fname = (doc.name+".pdf")
									with open(str(wts.document_download_path)+"/public/files/"+str(fname), "wb") as fp:
										fp.write(report)
									media_file_path = str(wts.document_download_path)+"/public/files/"+str(fname)
									access_token =frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token")
									api_base = "https://graph.facebook.com/v15.0"
									phone_number_id = wpid

									media_mime_type = mimetypes.guess_type(media_file_path)[0]

									# Way to send multi-part form data
									# Ref: https://stackoverflow.com/a/35974071
									form_data = {
										"file": (
											"file",
											open(media_file_path, "rb"),
											media_mime_type,
										),
										"messaging_product": (None, "whatsapp"),
										"type": (None, media_mime_type),
									}
									response = requests.post(
										f"{api_base}/{phone_number_id}/media",
										files=form_data,
										headers={
											"Authorization": "Bearer " + access_token,
										},
									)
									print("$$$$$$$$$$$$$$$$",response)
									if response.ok:
										url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
										payload2 = ""
										headers = {
											'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
											'Content-Type': 'application/json'
											}
										response = requests.request("GET", url2, headers=headers, data=payload2)

										d=eval(response.text)
										a=d.get("data")
										url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Notification"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
										payload3 = ""
										headers = {
											'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
											'Content-Type': 'application/json'
											}
										response = requests.request("GET", url4, headers=headers, data=payload3)
										c=eval(response.text)
										credit=c.get("data")
										url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
										payload4 = json.dumps({
											"data": {
												"project":wts.project_hash,
												"app":wts.app_hash,
												"customer":a.get("customer"),
												"api_call":"Media Upload",
												"api_call_url":url,
												"opening_credit":wts.current_credits,
												"credit_in":0,
												"credit_out":credit.get("credit_consumed")/credit.get("amount_per_credit"),
												"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
												"api_payload":payload1
												}
												})
										headers = {
											'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
											'Content-Type': 'application/json'
											}
										response = requests.request("POST", url3, headers=headers, data=payload4)
									else:
										frappe.log_error(title = 'Whatsapp Integration',message=response.message)

								wts = frappe.get_doc("Whatsapp Settings")         

								url = "https://graph.facebook.com/v15.0/{0}/messages".format(wts.phone_number_id)

							



								payload1= json.dumps({
									"recipient_type": "individual",
									"to":m_no,
									"type": "template",
									"messaging_product":"whatsapp",
									"template": {
											"name":  wtemplate.lower(),
											"language": {
												"code": "en"
											},
											"components": [
												{
												"type": "header",
												"parameters":[
													{
														"type": "document",
														"document": {
														"id": str(response.json().get("id")),
														"filename":str(doc.name)
														}
													}
												]
												},
												{
												"type": "body",
												"parameters": params
												}
											
											]
										}
								})
							# headers = {
							# 'Content-Type': 'application/json',
							# 'Authorization': 'Bearer {0}'.format(frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token"))
							# }

							# response = requests.request("POST", url, headers=headers, data=payload)
							# print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",response,response.content)
							url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
							payload2 = ""
							headers = {
								'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
								'Content-Type': 'application/json'
								}
							response = requests.request("GET", url2, headers=headers, data=payload2)

							d=eval(response.text)
							a=d.get("data")
							url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Notification"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
							payload3 = ""
							headers = {
								'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
								'Content-Type': 'application/json'
								}
							response = requests.request("GET", url4, headers=headers, data=payload3)
							c=eval(response.text)
							credit=c.get("data")
							url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
							payload4 = json.dumps({
								"data": {
									"project":wts.project_hash,
									"app":wts.app_hash,
									"customer":a.get("customer"),
									"api_call":"Notification",
									"api_call_url":url,
									"opening_credit":wts.current_credits,
									"credit_in":0,
									"credit_out":credit.get("credit_consumed")/credit.get("amount_per_credit"),
									"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
									"api_payload":payload1
									}
									})
							headers = {
								'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
								'Content-Type': 'application/json'
								}
							response = requests.request("POST", url3, headers=headers, data=payload4)
							
			except:
				traceback = frappe.get_traceback()
				frappe.log_error(title = 'Whatsapp Integration',message=traceback)
