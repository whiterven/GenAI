document.getElementById('upload-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData();
    const fileInput = document.getElementById('image-upload');
    const file = fileInput.files[0];
    formData.append('image', file);

    // Show loading state
    document.getElementById('loading').style.display = 'block';
    const progressBar = document.getElementById('progress-bar');
    let progress = 0;

    const interval = setInterval(function () {
        progress += 10;
        if (progress <= 100) {
            progressBar.style.width = progress + '%';
        } else {
            clearInterval(interval);
        }
    }, 300);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            clearInterval(interval);
            progressBar.style.width = '100%';
            document.getElementById('loading').style.display = 'none';

            if (data.success) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result-text').textContent = 'Image search completed successfully.';

                const resultLinks = document.getElementById('result-links');
                resultLinks.innerHTML = '';
                data.links.forEach(link => {
                    const a = document.createElement('a');
                    a.href = link.url;
                    a.textContent = link.title;
                    a.target = '_blank';
                    resultLinks.appendChild(a);
                });
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            clearInterval(interval);
            progressBar.style.width = '0';
            document.getElementById('loading').style.display = 'none';
            alert('An error occurred during the image search. Please try again.');
        });
});
