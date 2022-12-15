# Copyright (c) 2022, Dexciss Technology Pvt. Ltd. and contributors
# For license information, please see license.txt

from email import header
import frappe
from pymysql import NULL
import requests
import json
import os
from frappe.utils.data import flt

from frappe.model.document import Document

class WhatsappTemplate(Document):
	def validate(self):
		wts = frappe.get_doc("Whatsapp Settings")         
		if wts.enable==0:
			frappe.throw("First Enable Whatsapp Integration From Whatsapp Setting")
		url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Message"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
		payload3 = ""
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("GET", url4, headers=headers, data=payload3)
		c=eval(response.text)
		credit=c.get("data")
		x=flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
		if x<flt(wts.current_credits):
			frappe.throw("You doesn't Have Enough Credit")
	def before_cancel(self):
		wts = frappe.get_doc("Whatsapp Settings")

		name=self.name
		url = """https://graph.facebook.com/v15.0/{0}/message_templates?name={1}""".format(wts.business_account_id,name.lower())

		payload={}
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer {0}'.format(frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token"))
		}

		response = requests.request("DELETE", url, headers=headers, data=payload)
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
			url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
			payload3 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url4, headers=headers, data=payload3)
			c=eval(response.text)
			credit=c.get("data")
			doc=frappe.new_doc("Whatsapp Api Call Log")
			doc.api_call="Delete Template"
			doc.opening_credit=flt(wts.current_credits)
			doc.credit_in=0
			doc.credit_out=flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			doc.balance=flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			doc.save(ignore_permissions=True)
			url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
			payload4 = json.dumps({
				"data": {
					"project":wts.project_hash,
					"app":wts.app_hash,
					"customer":a.get("customer"),
					"api_call":"Template",
					"api_call_url":url,
					"opening_credit":flt(wts.current_credits),
					"credit_in":0,
					"credit_out":flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"api_payload":"Delete Template APi"
					}
					})
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("POST", url3, headers=headers, data=payload4)

	def before_submit(self):
		wts = frappe.get_doc("Whatsapp Settings")

		fields =[]
		for i in self.variables:
			full = "self" + "." + i.field_name
			fields.append(full)
		url = "https://graph.facebook.com/v15.0/{0}/message_templates".format(wts.business_account_id)
		name= self.name.lower()
		category = self.category
		body_text = self.body_text
		header_text = self.text
		footer_text = self.footer_text

		lang = self.language.replace("-","_")
		components = []
		pld = {}
		body = {}
		header = {}
		footer = {}
		buttons = {}

		if self.category:
			pld.update({
				"category":self.category
			})
		else:
			frappe.throw("Please Mention Template Category")
		
		if self.body_text:
			body.update({
				"type":"BODY",
				"text":"{0}".format(body_text)
			})
			components.append(body)
		
		if self.header == "Text":
			header.update({
				"type":"HEADER",
				"format":"TEXT",
				"text":"{0}".format(header_text),
				
			})

			components.append(header)
		if self.header == "Media":
			if self.media_type=="Image":
				header.update({
					
					"type": "HEADER",
					"format": "IMAGE"
			
				})
				components.append(header)
			if self.media_type=="Document":
				header.update({
					"type": "HEADER",
					"format": "Media",
					"type": "document",
					"document": {
					"id": "519992866836522",
					# filename is an optional parameter
					"filename": "xyz"
					}
							

				})
				components.append(header)
		if self.footer_text:
			footer.update({
				"type":"FOOTER",
				"text":"{0}".format(footer_text)
			})
			components.append(footer)
		if self.button_type in ("Call to Action","Quick Reply"):
			if self.button_type == "Call to Action":
				ph = self.dial_code + "" + self.phone_number
				
				buttons.update({
					"type":"BUTTONS",
					"buttons":[{"type":"PHONE_NUMBER","text":self.button_text,"phone_number":ph}]
						
				})
				components.append(buttons)
		
		
		
		
		pld.update({"components":components})
		pld.update({
			"name":"{0}".format(name),
			"language":"{0}".format(lang)
		})

	
		payload = json.dumps(pld)
		headers = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer {0}'.format(frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token"))
		}

		response =requests.request("POST", url, headers=headers, data=payload)
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
			url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
			payload3 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url4, headers=headers, data=payload3)
			c=eval(response.text)
			credit=c.get("data")
			doc=frappe.new_doc("Whatsapp Api Call Log")
			doc.api_call="Create Template"
			doc.opening_credit=flt(wts.current_credits)
			doc.credit_in=0
			doc.credit_out=flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			doc.balance=flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			doc.save(ignore_permissions=True)
			url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
			payload4 = json.dumps({
				"data": {
					"project":wts.project_hash,
					"app":wts.app_hash,
					"customer":a.get("customer"),
					"api_call":"Template",
					"api_call_url":url,
					"opening_credit":wts.current_credits,
					"credit_in":0,
					"credit_out":flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"api_payload":"Delete Template APi"
					}
					})
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("POST", url3, headers=headers, data=payload4)

		rc = json.loads(response.content)
		if response.status_code != 200:
			
			frappe.throw(rc["error"]["message"])
		else:
			frappe.msgprint("Template Created With Id - {0} ".format(name))

		

		
	


@frappe.whitelist()
def get_list(docname):
	from collections import OrderedDict
	import numpy as np
	print(docname)
	docfields = {
		
	}
	for row in frappe.get_all('DocField', fields = ['fieldname','label','fieldtype'],
		filters = {'parent': docname, 'fieldtype': ["not in",["Column Break","Section Break","Table"]]},order_by="fieldname asc"):

		docfields.update({
			row.label:[row.fieldname,row.fieldtype]
		})
	print("******************************************",docfields)
	
	return docfields
	

def status():
	wts = frappe.get_doc("Whatsapp Settings")

	url="https://graph.facebook.com/v14.0/{0}/message_templates?fields=name,status".format(wts.business_account_id)
	payload={}
	headers = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer {0}'.format(frappe.utils.password.get_decrypted_password("Whatsapp Settings", "Whatsapp Settings", "access_token"))
	}
	response = requests.request("GET", url, headers=headers, data=payload)
	data1=eval(response.text)
	id=frappe.db.sql("""select name from `tabWhatsapp Template` where docstatus=1 & status !="COMPLETED" """,as_dict=1)
	for i in id:
		for j in data1.get("data"):
			if str(i.name).lower()==j.get("name"):
				doc=frappe.get_doc("Whatsapp Template",i.name)
				doc.db_set('status', j.get("status"))
				frappe.db.commit()





		






			
			
		

		