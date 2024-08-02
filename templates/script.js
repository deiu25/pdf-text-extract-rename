function uploadFiles() {
    const uploadButton = document.getElementById('uploadBtn');
    const loader = document.getElementById('loader');
    uploadButton.disabled = true;
    loader.classList.remove('hidden');

    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files[]', files[i], files[i].name);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            let content = "";
            for (let i = 0; i < data.length; i++) {
                if (data[i].error) {
                    content += `<span class="text-red-500">${data[i].error}</span><br>`;
                } else {
                    content += `<span class="text-green-700">File processed: ${data[i].new_name}</span><br>`;
                }
            }
            document.getElementById('response').innerHTML = content;
            updateDownloadButton();
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            uploadButton.disabled = false;
            loader.classList.add('hidden');
        });
}


function updateDownloadButton() {
    fetch('/files-ready')
        .then(response => response.json())
        .then(data => {
            const downloadButton = document.getElementById('downloadAllBtn');
            if (data.all_files_ready) {
                downloadButton.classList.remove('hidden');
            } else {
                downloadButton.classList.add('hidden');
            }
        })
        .catch(error => console.error('Error:', error));
}

function downloadAll() {
    window.location.href = '/download-all';
    setTimeout(() => {
        fetch('/cleanup', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => console.log(data.message))
            .catch(error => console.error('Error:', error));
    }, 30000); // 30 de secunde
}
