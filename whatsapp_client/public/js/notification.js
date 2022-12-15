

frappe.ui.form.on("Notification", {

    refresh:function(frm){
        frm.set_query('whatsapp_template', function() {
			return {
				filters: {
					"status":"APPROVED",
					"docstatus": 1
				}
			}
		});
        if(frm.doc.channel=="Whatsapp B2C"){
                if (!frm.doc.document_type) {
                    return;
                }
                let get_select_options = function (df, parent_field) {
                    // Append parent_field name along with fieldname for child table fields
                    let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
    
                    return {
                        value: select_value,
                        label: df.fieldname + " (" + __(df.label) + ")",
                    };
                };
                let receiver_fields = [];
                let fields = frappe.get_doc("DocType", frm.doc.document_type).fields;
                if (in_list(["Whatsapp B2C"], frm.doc.channel)) {
                    receiver_fields = $.map(fields, function (d) {
                        return d.options == "Phone" ? get_select_options(d) : null;
                    });
                }
                console.log("**********************",receiver_fields)
                // set email recipient options
                frm.fields_dict.recipients.grid.update_docfield_property(
                    "receiver_by_document_field",
                    "options",
                    [""].concat(["owner"]).concat(receiver_fields)
                );
        }   
        
    },
    document_type:function(frm){
        if(frm.doc.channel=="Whatsapp B2C"){
            
                if (!frm.doc.document_type) {
                    return;
                }
                let get_select_options = function (df, parent_field) {
                    // Append parent_field name along with fieldname for child table fields
                    let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
    
                    return {
                        value: select_value,
                        label: df.fieldname + " (" + __(df.label) + ")",
                    };
                };
                let receiver_fields = [];
                let fields = frappe.get_doc("DocType", frm.doc.document_type).fields;
                if (in_list(["Whatsapp B2C"], frm.doc.channel)) {
                    receiver_fields = $.map(fields, function (d) {
                        return d.options == "Phone" ? get_select_options(d) : null;
                    });
                }
                console.log("**********************",receiver_fields)
                // set email recipient options
                frm.fields_dict.recipients.grid.update_docfield_property(
                    "receiver_by_document_field",
                    "options",
                    [""].concat(["owner"]).concat(receiver_fields)
                );
            
        }
    },
    whatsapp_template:function(frm){
        if(frm.doc.channel=="Whatsapp B2C"){
            if (!frm.doc.document_type) {
                return;
            }
            let get_select_options = function (df, parent_field) {
				// Append parent_field name along with fieldname for child table fields
				let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;

				return {
					value: select_value,
					label: df.fieldname + " (" + __(df.label) + ")",
				};
			};
            let receiver_fields = [];
            let fields = frappe.get_doc("DocType", frm.doc.document_type).fields;
            if (in_list(["Whatsapp B2C"], frm.doc.channel)) {
                receiver_fields = $.map(fields, function (d) {
                    return d.options == "Phone" ? get_select_options(d) : null;
                });
            }
            console.log("**********************",receiver_fields)
            // set email recipient options
            frm.fields_dict.recipients.grid.update_docfield_property(
                "receiver_by_document_field",
                "options",
                [""].concat(["owner"]).concat(receiver_fields)
            );
        
        }
    },
    channel:function(frm){
        if(frm.doc.channel=="Whatsapp B2C"){
            if (!frm.doc.document_type) {
                return;
            }
            let get_select_options = function (df, parent_field) {
				// Append parent_field name along with fieldname for child table fields
				let select_value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;

				return {
					value: select_value,
					label: df.fieldname + " (" + __(df.label) + ")",
				};
			};
            let receiver_fields = [];
            let fields = frappe.get_doc("DocType", frm.doc.document_type).fields;
            if (in_list(["Whatsapp B2C"], frm.doc.channel)) {
                receiver_fields = $.map(fields, function (d) {
                    return d.options == "Phone" ? get_select_options(d) : null;
                });
            }
            console.log("**********************",receiver_fields)
            // set email recipient options
            frm.fields_dict.recipients.grid.update_docfield_property(
                "receiver_by_document_field",
                "options",
                [""].concat(["owner"]).concat(receiver_fields)
            );
        
        }
    }

})