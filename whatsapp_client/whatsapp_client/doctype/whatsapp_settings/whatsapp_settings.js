// Copyright (c) 2022, Ajay and contributors
// For license information, please see license.txt

frappe.ui.form.on('Whatsapp Settings', {
	buy_credit: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "create_payment_link",
			callback:function(r){
				
			}
		  })
	}
});
