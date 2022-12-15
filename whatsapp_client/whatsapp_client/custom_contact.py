import frappe





def set_primary(self,method):
    # Used to set primary mobile and phone no.
    fieldname="whatsapp_no"
    if len(self.phone_nos) == 0:
        setattr(self, fieldname, "")
        return

    field_name = "is_whatsapp_number"

    is_primary = [phone.phone for phone in self.phone_nos if phone.get(field_name)]

    if len(is_primary) > 1:
        frappe.throw(
            _("Only one {0} can be set as primary.").format(frappe.bold(frappe.unscrub(fieldname)))
        )

    primary_number_exists = False
    for d in self.phone_nos:
        if d.get(field_name) == 1:
            primary_number_exists = True
            setattr(self, fieldname, d.phone)
            break

    if not primary_number_exists:
        setattr(self, fieldname, "")