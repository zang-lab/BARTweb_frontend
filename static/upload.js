

$(document).ready(function() {
	

	$('#inputForm').on('submit', function(event) {

		//If the input is not 
		var dataType = $("input[name=dataType]").filter(":checked").val()
		if (dataType === "Geneset" ){
			return
		}

		// will not preform redirect(url_for('get_result', user_key=user_key))
		event.preventDefault();

		var formData = new FormData();
		//console.log(formData)
		var fileInput = document.getElementById('uploadFilesProfile');
 		var file = fileInput.files[0];
 		console.log(fileInput);
 		console.log(file);
 		formData.append('uploadFilesProfile',file);

 		formData.append("submit_button", "predict_data");
    formData.append("username", document.getElementById("username").value);
    formData.append("jobname", document.getElementById("jobname").value);
    formData.append("species", $("input[name=species]").filter(":checked").val());
    formData.append("dataType", $("input[name=dataType]").filter(":checked").val());


    var uniqueNum = new Date().valueOf();
    var userEmail = document.getElementById('username').value;
    var jobName = document.getElementById('jobname').value;
    var username = "";
    if (jobName === "") {
      if (userEmail === "") {
        username = "anonymous";
      } 
      else {
        username = userEmail.split("@")[0]; // get user e-mail
      }
    } else {
      username = jobName.replace(" ", ""); // remove whitespace
    }
    var userkey = username + '_' + uniqueNum;
    formData.append("userkey", userkey);

		
 		for (var pair of formData.entries()){
 			console.log(pair[0]+', '+pair[1]);
 		}

		$.ajax({
			xhr : function() {
				var xhr = new window.XMLHttpRequest();
				console.log(xhr)

				xhr.upload.addEventListener('progress', function(e) {
					console.log(e.lengthComputable)
					if (e.lengthComputable) {

						console.log('Bytes Loaded: ' + e.loaded);
						console.log('Total Size: ' + e.total);
						console.log('Percentage Uploaded: ' + (e.loaded / e.total))

						var percent = Math.round((e.loaded / e.total) * 100);

						$('#progressBar').attr('aria-valuenow', percent).css('width', percent + '%').text(percent + '%');

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