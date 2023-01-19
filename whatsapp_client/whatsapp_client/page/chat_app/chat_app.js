// frappe.pages['chat_app'].on_page_load = function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'chat_app',
// 		single_column: true
// 	});
// }


frappe.pages['chat_app'].on_page_load = function(wrapper) {
	new MyPage(wrapper);
	
	
}

MyPage = Class.extend({
	init : function (wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'New Chat App',
			single_column: true
		});
		this.make() ;
		
	},

	

	make: function () {
		
		let me = $(this);
		
		let body = `
		
					<div style="max-height:700px;">
						<div class="row" style="height:800px; max-height:800px;" >
							<div class="col-lg-4" style="border:none;box-shadow: 0px 0px 6px 0px lightgray;border-radius:5px;">
							<div style="position:fixed;bottom:52px;right:70%;left:34%;margin:20px;height:50px;width:60px;z-index:1;">
							<p style="font-size:50px;background:#0095ff;color:white;border-radius:50%;text-align:center;">+</p>
							</div>
								<div><input placeholder="Search here" type="text" style="border:none;box-shadow: 0px 0px 2px 0px lightgray;border-radius:5px;background:#ebebeb;margin:auto;width:100%;padding:10px;margin:30px auto 30px auto;outline: none;"></div>
								<div class="chatlist" style="position: static;height: calc(100% - 110px);overflow-y: auto;">
								   <div class="block" style="position: static;width: 100%;display: flex;justify-content: center;align-items: center;padding: 20px 15px 20px 15px;border-bottom: 1px solid rgba(0,0,0,0.06);">
										<div class="imgbx" style=" position: relative;  min-width: 45px;  height: 45px;  overflow: hidden;  border-radius: 50%;  margin-right: 10px;">
											<img src="assets/chat_ui/img/me.png" class="cover" style="position: absolute;top: 0;left: 0;width: 100%;height: 100%;object-fit: cover;" >
										</div>
										<div class="details" style="position: relative;  width: 100%;">
											<div class="listHead" style=" display: flex;justify-content: space-between;margin-bottom: 5px;">
											<h4 style="font-size: 1.1em;  font-weight: 600;  color: black;" >Amit ji</h4>
											<p class="time" style="font-size: 0.75em;color: #aaa;">10:16</p>
											</div>
											<div class="message_p" style=" display: flex;	justify-content: space-between;	align-items: center;">
												<p style="color: #aaa;  display: -webkit-box;  -webkit-line-clamp: 1;  font-size: 0.9em;  -webkit-box-orient: vertical;   text-overflow: ellipsis;">How to make whatsapp?</p>
												<b style="background: #06d755;color: #fff;min-width: 20px;height: 20px;border-radius: 50%;display: flex;justify-content: center;align-items: center;font-size: 0.75em;" >1</b>
											</div>
								  		</div>
									</div>
							 	</div>
							</div>

							<div class="col-lg-7" style="border:none;box-shadow: 0px 0px 6px 0px #ebebeb;border-radius:10px;margin:0px 20px;padding:0px;width:auto;">
								<header style="position:sticky;width: 100%;height: 90px;display: flex;justify-content: space-between;padding: 30px 15px 0px 15px;margin-top:auto;margin-bottom:auto;background: linear-gradient(lightgray 0%,lightgray 100px, white 100px, white 100%);border-radius:6px 6px 0px 0px;">
								<div class="row">
									<img src="" alt="#" style="width:60px;height:50px; border:0.5px solid; margin:-8px 30px 0px 30px;">
									<h4 style="font-size:20px;"><b>Name of userrrrrrrrrrrrr</b></h4>
								</div>
								</header>
								
								
								<div style="margin:0px 10px;">
								<div>
								<div style="background-color:lightyellow; margin-left:50px;float:right;margin-top:5px;margin-bottom:5px;padding:10px;max-width:60%;">
								<p >My msgggggggggg gggggggggggg ggggggggg gggggggggggggggggggggggggggggggggg ggg gg gg gg gg ggg ggg gg ggg</p>
								<p style="position:static;text-align:right;">10:56</p>
								</div>
								</div>
								
								<div>
								<div style="background-color:lightcyan; margin-right:50px;float:left;margin-top:5px;margin-bottom:5px;padding:10px;max-width:60%;">
								<p>My msgggggggggg gggggggggggg ggggggggg gggggggggggggggggggggggggggggggggg ggg gg gg gg gg ggg ggg gg ggg</p>
								<p style="position:static;text-align:right;">14:22</p>
								</div>
								</div>
								</div>
								<div class="row" style="bottom:70px;max-width:80%;width:720px; margin-left:10px;margin-right:5px;height:50px; border-radius:20px;position:fixed;border-bottom:1px solid;padding-left:10px;">
									<div class="col-lg-12 col-md-12 col-sm-12">
									<input placeholder="Type your message here" style="max-width:870px;border:none;outline:none;background:none;font-size:20px;"><img src="" alt="Send" style="padding-right:15px;float:right;"><img src="" alt="Attach" style="padding-right:15px;float:right;">
									</div>
								</div>
							<div>
						</div> 
					</div>
					
					`

			
		
		$(frappe.render_template(body, this)).appendTo(this.page.main)
	}
	

})
