document.addEventListener('DOMContentLoaded', function() {
    // By default, load edit and like functions
    editPost();
    likeCount();
});

    function editPost(){

        document.querySelectorAll(".content-input").forEach(form => {
            form.style.display="none";
        });

        // Listen for click on edit button for each post
        document.querySelectorAll("#edit").forEach(editButton => {
            editButton.addEventListener("click", function() {

                // Get current post.id
                const postId = editButton.dataset.post;

                // Create variables referencing current text div and input div
                const content = document.querySelector(`.content[data-post="${postId}"]`);
                const inputForm = document.querySelector(`.content-input[data-post="${postId}"]`);

                // Hide current post content and edit button
                content.style.display = "none";
                editButton.style.display = "none";

                // Show div containing input form and post button
                inputForm.style.display = "block";

                // Reference textarea, populate with existing post content
                const textArea = document.querySelector(`.textarea[data-post="${postId}"]`);
                textArea.innerText = content.innerText;

                // Listen for click on Post button
                document.querySelector(`.btn.btn-primary[id="${postId}"]`).addEventListener("click", function() {

                    // Get new input from text-area
                    const contentInput = textArea.value;

                    // Create reference to CSRF token
                    const token = document.querySelector("input[name='csrfmiddlewaretoken']").value;

                    // Make PUT request to update current-post in database
                    fetch("/post/" + postId, {
                        method: "PUT",
                        headers: {
                            "X-CSRFToken": token,
                        },
                        body: JSON.stringify({
                            content: contentInput
                        })
                    })
                    .then(response => {
                        if (!response.ok){
                            throw Error();
                        }else{
                            response.json();
                            // Set content of original post to new content
                            content.innerHTML = contentInput;
                            // Hide textarea and post button, show new content and edit button
                            inputForm.style.display="none";
                            content.style.display="block";
                            editButton.style.display="block";
                        }
                    }).catch(() => {
                        alert("Post Failed To Update.");
                    });
                });
            });
        });
    }

    function likeCount(){

        // Listen for click on heart image on each post
        document.querySelectorAll(".heart").forEach(div => {
            div.addEventListener("click", function() {
                
                // Create reference to like counter
                const postId = div.dataset.post;
                const counter = document.querySelector(`.counter[data-post="${postId}"]`);    

                // Create reference to CSRF token
                const token = document.querySelector("input[name='csrfmiddlewaretoken']").value; 

                // Send post request to generate new 'like' instance in database
                fetch("/like-post", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": token,
                    },
                    body: JSON.stringify({
                        post: postId
                    })
                })
                .then(response => response.json())
                .then(result => {
                    // Set innerHTML of counter to new total count value
                    counter.innerHTML = result.newCount;
                }).catch(() => {
                    console.log("Like failed.");
                });
            });
        });
    }

