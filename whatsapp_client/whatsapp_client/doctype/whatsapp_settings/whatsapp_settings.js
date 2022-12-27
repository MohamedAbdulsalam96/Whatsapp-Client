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
	},
	credit: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "get_rate_amount",
			callback:function(r){
				if(r.message){
					frm.refresh_field("rate")
					frm.refresh_field("amount")
				}
				
			}
		  })
	},
	refresh: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "get_credit",
			callback:function(r){
				if(r.message){
				}
				
			}
		  })
	}
});
