# Copyright (c) 2022, Hussain Nagaria and contributors
# For license information, please see license.txt

import frappe
import requests
import mimetypes

from typing import Dict
from functools import lru_cache
from frappe.model.document import Document
from frappe.utils.data import flt


MEDIA_TYPES = ("image", "sticker", "document", "audio", "video")


class WhatsAppMessages(Document):
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
		self.validate_image_attachment()

		if self.message_type == "Audio" and self.media_file:
			self.preview_html = f"""
				<audio controls>
					<source src="{self.media_file}" type="{self.media_mime_type}">
					Your browser does not support the audio element.
				</audio>
			"""

		if self.message_type == "Video" and self.media_file:
			self.preview_html = f"""
				<video controls>
					<source src="{self.media_file}" type="{self.media_mime_type}">
					Your browser does not support the video element.
				</video>
			"""

	def validate_image_attachment(self):
		if self.media_image:
			self.media_file = self.media_image

		if self.media_file and self.message_type == "Image":
			self.media_image = self.media_file

	@frappe.whitelist()
	def send(self) -> Dict:
		if not self.to:
			frappe.throw("Recepient (`to`) is required to send message.")

		access_token = frappe.utils.password.get_decrypted_password(
			"Whatsapp Settings", "Whatsapp Settings", "access_token"
		)
		api_base = "https://graph.facebook.com/v15.0"
		phone_number_id = frappe.db.get_single_value("Whatsapp Settings", "phone_number_id")

		endpoint = f"{api_base}/{phone_number_id}/messages"

		response_data = {
			"messaging_product": "whatsapp",
			"recipient_type": "individual",
			"to": self.to,
			"type": self.message_type.lower(),
		}
		print(response_data)
		if self.message_type == "Text":
			response_data["text"] = {"preview_url": False, "body": self.message_body}

		if self.message_type in ("Audio", "Image", "Video", "Document"):
			if not self.media_id:
				frappe.throw("Please attach and upload the media before sending this message.")

			response_data[self.message_type.lower()] = {
				"id": self.media_id,
			}

			if self.message_type == "Document":
				response_data[self.message_type.lower()]["filename"] = self.media_filename
				response_data[self.message_type.lower()]["caption"] = self.media_caption
		url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
		payload2 = ""
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("GET", url2, headers=headers, data=payload2)

		d=eval(response.text)
		a=d.get("data")
		url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Message"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
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
				"api_call":"Message",
				"api_call_url":endpoint,
				"opening_credit":wts.current_credits,
				"credit_in":0,
				"credit_out":credit.get("credit_consumed")/credit.get("amount_per_credit"),
				"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
				"api_payload":response_data
				}
				})
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("POST", url3, headers=headers, data=payload4)

		# response = requests.post(
		# 	endpoint,
		# 	json=response_data,
		# 	headers={
		# 		"Authorization": "Bearer " + access_token,
		# 		"Content-Type": "application/json",
		# 	},
		# )
		# if response.ok:
		# 	self.id = response.json().get("messages")[0]["id"]
		# 	self.status = "Sent"
		# 	self.save(ignore_permissions=True)
		# 	return response.json()
		# else:
		# 	frappe.throw(response.json().get("error").get("message"))

	@frappe.whitelist()
	def download_media(self) -> Dict:
		url = self.get_media_url()
		access_token = self.get_access_token()
		response = requests.get(
			url,
			headers={
				"Authorization": "Bearer " + access_token,
			},
		)

		file_name = get_media_extention(self, response.headers.get("Content-Type"))
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": response.content,
				"attached_to_doctype": "WhatsApp Messages",
				"attached_to_name": self.name,
				"attached_to_field": "media_file",
			}
		).insert(ignore_permissions=True)

		self.set("media_file", file_doc.file_url)

		# Will be used to display image preview
		if self.message_type == "Image":
			self.set("media_image", file_doc.file_url)

		self.save()

		return file_doc.as_dict()

	def get_media_url(self) -> str:
		if not self.media_id:
			frappe.throw("`media_id` is missing.")

		api_base = "https://graph.facebook.com/v15.0"
		access_token = self.get_access_token()
		response = requests.get(
			f"{api_base}/{self.media_id}",
			headers={
				"Authorization": "Bearer " + access_token,
			},
		)

		if not response.ok:
			frappe.throw("Error fetching media URL")

		return response.json().get("url")

	@lru_cache
	def get_access_token(self) -> str:
		return frappe.utils.password.get_decrypted_password(
			"Whatsapp Settings", "Whatsapp Settings", "access_token"
		)

	@frappe.whitelist()
	def upload_media(self):
		wts = frappe.get_doc("Whatsapp Settings")
		if not self.media_file:
			frappe.throw("`media_file` is required to upload media.")

		media_file_path = frappe.get_doc(
			"File", {"file_url": self.media_file}
		).get_full_path()
		access_token = self.get_access_token()
		api_base = "https://graph.facebook.com/v15.0"
		phone_number_id = frappe.db.get_single_value("Whatsapp Settings", "phone_number_id")

		if not self.media_mime_type:
			self.media_mime_type = mimetypes.guess_type(self.media_file)[0]

		# Way to send multi-part form data
		# Ref: https://stackoverflow.com/a/35974071
		form_data = {
			"file": (
				"file",
				open(media_file_path, "rb"),
				self.media_mime_type,
			),
			"messaging_product": (None, "whatsapp"),
			"type": (None, self.media_mime_type),
		}
		
		response = requests.post(
			f"{api_base}/{phone_number_id}/media",
			files=form_data,
			headers={
				"Authorization": "Bearer " + access_token,
			},
		)

		if response.ok:
			self.media_id = response.json().get("id")
			self.media_uploaded = True
			self.save(ignore_permissions=True)
			url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
			payload2 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url2, headers=headers, data=payload2)

			d=eval(response.text)
			a=d.get("data")
			url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],["`tabRate Card`.api_call","=","Message"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
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
					"api_call_url":str(api_base)+str(phone_number_id)+"media",
					"opening_credit":wts.current_credits,
					"credit_in":0,
					"credit_out":credit.get("credit_consumed")/credit.get("amount_per_credit"),
					"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"api_payload":form_data
					}
					})
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("POST", url3, headers=headers, data=payload4)
		else:
			frappe.throw(response.json().get("error").get("message"))

	@frappe.whitelist()
	def mark_as_seen(self):
		wts = frappe.get_doc("Whatsapp Settings")
		if self.type != "Incoming":
			frappe.throw("Only incoming messages can be marked as seen.")

		phone_number_id = frappe.db.get_single_value("Whatsapp Settings", "phone_number_id")
		endpoint = f"https://graph.facebook.com/v15.0/{phone_number_id}/messages"
		access_token = self.get_access_token()
		response = requests.post(
			endpoint,
			json={"messaging_product": "whatsapp", "status": "read", "message_id": self.id},
			headers={
				"Authorization": "Bearer " + access_token,
				"Content-Type": "application/json",
			},
		)

		if response.ok:
			self.status = "Marked As Seen"
			self.save()
			url2="""https://erp.dexciss.com/api/resource/Subscription%20Project?filters=[["name","=","{0}"], ["app","=","{1}"]]&fields=["*"]""".format(wts.project_hash,wts.app_hash)
			payload2 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url2, headers=headers, data=payload2)

			d=eval(response.text)
			a=d.get("data")
			url4="""https://erp.dexciss.com/api/resource/Subscription%20App?filters=[["name","=","{0}"],,["`tabRate Card`.api_call","=","Seen"]]&fields=["amount_per_credit","`tabRate Card`.api_call","`tabRate Card`.credit_consumed"]""".format(wts.app_hash)
			payload3 = ""
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("GET", url4, headers=headers, data=payload3)
			c=eval(response.text)
			credit=c.get("data")
			doc=frappe.new_doc("Whatsapp Api Call Log")
			doc.api_call="Seen"
			doc.opening_credit=flt(wts.current_credits)
			doc.credit_in=0
			doc.credit_out=flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit"))
			doc.balance=flt(wts.current_credits)-flt(doc.credit_out)
			doc.save(ignore_permissions=True)
			url3="https://erp.dexciss.com/api/resource/Subcription%20App%20API%20Log"
			payload4 = json.dumps({
				"data": {
					"project":wts.project_hash,
					"app":wts.app_hash,
					"customer":a.get("customer"),
					"api_call":"Seen",
					"api_call_url":endpoint,
					"opening_credit":flt(wts.current_credits),
					"credit_in":0,
					"credit_out":flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"balance":flt(wts.current_credits)-flt(credit.get("credit_consumed"))/flt(credit.get("amount_per_credit")),
					"api_payload":json
					}
					})
			headers = {
				'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
				'Content-Type': 'application/json'
				}
			response = requests.request("POST", url3, headers=headers, data=payload4)
			
		else:
			frappe.throw(response.json().get("error").get("message"))


def create_whatsapp_message(message: Dict) -> WhatsAppMessages:
	message_type = message.get("type")

	# Create whatsapp contact doc if not exists
	received_from = message.get("from")
	if not frappe.db.exists("WABA WhatsApp Contact", {"name": received_from}):
		frappe.get_doc(
			{
				"doctype": "WABA WhatsApp Contact",
				"whatsapp_id": received_from,
			}
		).insert(ignore_permissions=True)

	message_data = frappe._dict(
		{
			"doctype": "WhatsApp Messages",
			"type": "Incoming",
			"status": "Received",
			"from": message.get("from"),
			"id": message.get("id"),
			"message_type": message_type.title(),
		}
	)

	if message_type == "text":
		message_data["message_body"] = message.get("text").get("body")
	elif message_type in MEDIA_TYPES:
		message_data["media_id"] = message.get(message_type).get("id")
		message_data["media_mime_type"] = message.get(message_type).get("mime_type")
		message_data["media_hash"] = message.get(message_type).get("sha256")

	if message_type == "document":
		message_data["media_filename"] = message.get("document").get("filename")
		message_data["media_caption"] = message.get("document").get("caption")

	message_doc = frappe.get_doc(message_data).insert(ignore_permissions=True)

	wants_automatic_image_downloads = frappe.db.get_single_value(
		"Whatsapp Settings", "automatically_download_images"
	)

	wants_automatic_audio_downloads = frappe.db.get_single_value(
		"Whatsapp Settings", "automatically_download_audio"
	)
	wants_automatic_video_downloads = frappe.db.get_single_value(
		"Whatsapp Settings", "automatically_download_videos"
	)
	if (message_doc.message_type == "Image" and wants_automatic_image_downloads) or (
		message_doc.message_type == "Audio" and wants_automatic_audio_downloads
	) or (message_doc.message_type == "Video" and wants_automatic_video_downloads
	):
		try:
			current_user = frappe.session.user
			frappe.set_user("Administrator")
			message_doc.download_media()
			frappe.set_user(current_user)
		except:
			frappe.log_error(
				f"WABA: Problem downloading {message_doc.message_type}", frappe.get_traceback()
			)

	return message_doc


def process_status_update(status: Dict):
	message_id = status.get("id")
	status = status.get("status")

	frappe.db.set_value(
		"WhatsApp Messages", {"id": message_id}, "status", status.title()
	)


def get_media_extention(message_doc: WhatsAppMessage, content_type: str) -> str:
	return message_doc.media_filename or (
		"attachment_." + content_type.split(";")[0].split("/")[1]
	)
