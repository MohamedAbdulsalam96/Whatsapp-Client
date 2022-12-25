# Copyright (c) 2022, Ajay and contributors
# For license information, please see license.txt

import requests
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


	def get_credit(self):
		wts = frappe.get_doc("Whatsapp Settings")  
		url2="""https://erp.dexciss.com/api/resource/Payment%20Request/"""
		payload2 = ""
		headers = {
			'Authorization': 'token {0}:{1}'.format(wts.api_key,wts.get_password("api_secret")),
			'Content-Type': 'application/json'
			}
		response = requests.request("GET", url2, headers=headers, data=payload2)
		

	
	@frappe.whitelist()
	def get_rate_amount(self):
		wts = frappe.get_doc("Whatsapp Settings")  

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
		cred=c.get("data")
		self.db_set('rate', cred.amount_per_credit)
		self.db_set('amount', self.credit *cred.amount_per_credit)
		return True
