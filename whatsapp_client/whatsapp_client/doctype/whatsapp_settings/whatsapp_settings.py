# Copyright (c) 2022, Ajay and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WhatsappSettings(Document):
	@frappe.whitelist()
	def create_payment_link(self):
		wts = frappe.get_doc("Whatsapp Settings")  
		url2="""https://erp.dexciss.com/api/method/subscription.subscription.doctype.subscription_project.subscription_project.generate_link?amount={0}&project_hash={1}""".format(wts.amount,wts.project_hash)
		payload2 = ""
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("GET", url2, headers=headers, data=payload2)
		if response.ok:
			d=eval(response.text)
			import urllib.request  
			webUrl = urllib.request.urlopen(str(d.get("url")))  

		url2="""https://erp.dexciss.com/api/"""
		payload2 = ""
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("GET", url2, headers=headers, data=payload2)

