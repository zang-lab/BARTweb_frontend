$(document).ready(function() {
	// on form submit
	$('#inputForm').on('submit', function(event) {

		//If the input data type is gene list
		var dataType = $('select[name=dataType]').val()
		if (dataType === "Geneset" ){
			return
		}
		if (dataType === "HiC" ){
			return
		}
		//If the input profile type is empty
		if (dataType=='ChIP-seq' && document.getElementById('uploadFilesProfile').value == "") {
            return
        }
        if (dataType=='regions' && document.getElementById('uploadFilesRegions').value == "") {
            return
        }

		// will not preform redirect(url_for('get_result', user_key=user_key))
		event.preventDefault();

		var formData = new FormData();
		// append file object to formData
		if (dataType=='ChIP-seq') {
            var fileInput = document.getElementById('uploadFilesProfile');
 			var file = fileInput.files[0];
			formData.append('uploadFilesProfile',file);
        }
		if (dataType=='regions') {
            var fileInput = document.getElementById('uploadFilesRegions');
 			var file = fileInput.files[0];
			formData.append('uploadFilesRegions',file);
        }

		// get form data and append to formData
		var userEmail = document.getElementById('useremail').value;
		var jobName = document.getElementById('jobname').value;
		var species = $("input[name=species]").filter(":checked").val();
		var dataType = $('select[name=dataType]').val();

 		formData.append("submit_button", "predict_data");
		formData.append("useremail", userEmail);
		formData.append("jobname", jobName);
		formData.append("species", species);
		formData.append("dataType", dataType);

		// generate user key based on timestamp and append to formData
		userkey = generateUserkey(userEmail, jobName);
		formData.append("userkey", userkey);
	
		for (var pair of formData.entries()){
			//console.log(pair[0]+', '+pair[1]);
		}

		// ajax post request passing form data information to flask
		$.ajax({
			xhr : function() {
				var xhr = new window.XMLHttpRequest();
				xhr.upload.addEventListener('progress', function(e) {
					console.log(e.lengthComputable)
					$('#progressBar').removeAttr('hidden');
					if (e.lengthComputable) {
						// console.log('Bytes Loaded: ' + e.loaded);
						// console.log('Total Size: ' + e.total);
						// console.log('Percentage Uploaded: ' + (e.loaded / e.total))
						var percent = Math.round((e.loaded / e.total) * 100);
						$('#progressBar').attr('aria-valuenow', percent).css('width', percent + '%').text(percent + '%');
					}
					// TODO: what if file not computable? Need to make a fake one...
					else {

					}
				});

				return xhr;
			},
			type : 'POST',
			url : '/',
			data : formData,
			processData : false,
			contentType : false,
			success : function() {
				window.location.href = "/result?user_key=" + this.data.get("userkey");
			}
		});
	});

});

// generate user key based on timestamp
function generateUserkey(userEmail, jobName) {
	var uniqueNum = new Date().valueOf();
	var userkeyPrefix = "";
    // jobName has a higher priority than userEmail on generating userkey
	if (jobName === "") {
		if (userEmail === "") {
			userkeyPrefix = "anonymous";
		} 
		else {
			userkeyPrefix = userEmail.split("@")[0]; // get user e-mail name
		}
	} 
	else {
		userkeyPrefix = jobName.replace(" ", ""); // remove whitespace if exists
	}

	var userkey = userkeyPrefix + '_' + uniqueNum;
	return userkey;
}