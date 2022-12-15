# Copyright (c) 2022, Ajay and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WhatsappApiCallLog(Document):
	def before_save(self):
		doc = frappe.get_doc("Whatsapp Settings")

		if self.credit_out>0:
			doc.current_credits=str(flt(doc.current_credits)-flt(self.credit_out))
			doc.save(ignore_permissions=True)
		if self.credit_in>0:
			doc.current_credits=str(flt(doc.current_credits)-flt(self.credit_in))
			doc.save(ignore_permissions=True)
