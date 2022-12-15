import frappe
from whatsapp_integration.whatsapp_integration.doctype.whatsapp_message.whatsapp_message import (
	create_whatsapp_message,
	process_status_update,
)

from werkzeug.wrappers import Response


@frappe.whitelist(allow_guest=True)
def handle():
	if frappe.request.method == "GET":
		return verify_token_and_fulfill_challenge()

	try:
		form_dict = frappe.local.form_dict
		messages = form_dict["entry"][0]["changes"][0]["value"].get("messages", [])
		statuses = form_dict["entry"][0]["changes"][0]["value"].get("statuses", [])

		for status in statuses:
			process_status_update(status)

		for message in messages:
			create_waba_whatsapp_message(message)

		frappe.get_doc(
			{"doctype": "Whatsapp Webhook Log", "payload": frappe.as_json(form_dict)}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error("Whatsapp Webhook Log Error", frappe.get_traceback())
		frappe.throw("Something went wrong")


def verify_token_and_fulfill_challenge():
	meta_challenge = frappe.form_dict.get("hub.challenge")
	expected_token = frappe.db.get_single_value("Whatsapp Settings", "webhook_verify_token")

	if frappe.form_dict.get("hub.verify_token") != expected_token:
		frappe.throw("Verify token does not match")

	return Response(meta_challenge, status=200)
