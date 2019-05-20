

$(document).ready(function() {
	

	$('#inputForm').on('submit', function(event) {

		event.preventDefault();

		var formData = new FormData();
		//console.log(formData)
		var fileInput = document.getElementById('uploadFilesProfile');
 		var file = fileInput.files[0];
 		console.log(fileInput);
 		console.log(file);
 		formData.append('file',file);
		
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
				//$('#inputForm').submit();
			}
		});
		

	});

});