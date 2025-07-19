
document.addEventListener('DOMContentLoaded', () => {

    //updating the chat with new messages
    const chatMessages = document.getElementById('chatMessages');

    function addMessage(text, user = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${user ? 'user' : 'other'}`;
        messageDiv.innerHTML = `<div class="message-text">${text}</div>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
    }

    function addAudioMessage(filename, user = true) {
        if (chatMessages) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${user ? 'user' : 'other'}`;
            messageDiv.innerHTML = `<audio controls class="message-text message-audio">
                                        <source src="/audio_folder/${filename}" type="audio/wav">
                                    </audio>`;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
        }
    }

    function dynAddAudioMessage(audio, user = true) {
        const messageDiv = document.createElement('div');

        const audioURL = URL.createObjectURL(audio);

        messageDiv.className = `message ${user ? 'user' : 'other'}`;
        messageDiv.innerHTML = `<audio controls class="message-text message-audio">
                                    <source src="${audioURL}" type="audio/wav">
                                </audio>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;   
    }

    fetch('/check-database')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        // Create an array of objects with keys id, user, and machine
        const chatDataArray = data.map(item => ({
            id: item.id || 'N/A',        // Handle missing data
            user: item.user || 'N/A',    // Handle missing data
            machine: item.machine || 'N/A' // Handle missing data
        }));

        // Populate chatMessages with entries from chatDataArray
        chatDataArray.forEach(entry => {
            const text = `${entry.user}`;
            if (text.endsWith(".wav")) {
                addAudioMessage(text, true);
            } else {
                // Assuming user flag can be determined based on some logic, for now set as true for all
                addMessage(text, true);
            }

            const text2 = `${entry.machine}`;
            addMessage(text2, false);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });

    const startChatForms =  document.querySelectorAll('.startChatForm');

    let containerContent = '';
    let container = ''; 

    startChatForms.forEach(startChatForm => {
        startChatForm.addEventListener('submit', function(event) {
            console.log("the form data will be submitted")
            //prevents the default form submission, allowing custom handling of the form data
            event.preventDefault(); // Prevent the default form submission

            document.getElementById('audioForm').style.display = 'none';
            document.getElementById('againButton').style.display = 'none';
            document.getElementById('delButton').style.display = 'none';
            document.getElementById('audioPlayer').style.display = 'none';

            // Prepare the form data
            //this refers to the form being submitted, which will be sent in the AJAX request
            const formData = new FormData(this);
            document.getElementById("recordButton").style.display = "none";
            if (formData.get("messageInput")) {
                const messageInput = formData.get("messageInput");
                addMessage(messageInput);

                //insert the loading wheel inside this innerHTML
                container = document.querySelector('.messageContainer');
                containerContent = document.querySelector('.messageContainer').innerHTML;
                console.log(containerContent);
                container.innerHTML = `<div class="spinner-grow" id="loadingWheel" role="status" style="margin: 20px">
                                            <span class="sr-only">Loading...</span>
                                        </div>`;

            } else if (formData.get("question")) {
                //insert the loading wheel inside this innerHTML
                container = document.querySelector('.messageContainer');
                containerContent = document.querySelector('.messageContainer').innerHTML;
                console.log(containerContent);
                container.innerHTML = `<div class="spinner-grow" id="loadingWheel" role="status" style="margin: 20px">
                                            <span class="sr-only">Loading...</span>
                                        </div>`;
            } else {
                const file = formData.get("audioStorage");
                if (file) {    
                    addAudioMessage(file.name);
                    //insert the loading wheel inside this innerHTML
                    document.getElementById('loadingWheel').style.display = 'block';
                } else {
                    console.log("no audio file");
                }
            }
            //empty variable to store the URL to which the request will be sent
            let route = '';
    
            let value = document.getElementById('value');
            if (value.value === "1") {
                route = '/start_chat_page';
            } else if (value.value === "2") {
                route = '/chat_page';
                console.log("fetching to the /chat_page route");
            }
            // Create an AJAX request
            fetch(route, {
                method: 'POST',
                //the formData is sent to the route with method POST
                //the data is being processed by the route functions without the refreshing of the page
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                // Handle the server response
                return response.json(); // or response.text() if not JSON
            })
            .then(data => {
                // Process the response data (the return value of the response part)
                console.log('Success:', data);
                if (data.redirect) {
                    // Redirect to the specified URL
                    window.location.href = data.redirect;
                } else if (data.message) {
                    console.log("the machine has generated some answers");
                    addMessage(data.message, false);
                }
            })
            .catch(error => {
                // Handle errors
                console.error('Error:', error);
            })
            .finally(() => {
                //reinsert the send button at the place of the loadingWheel 
                document.getElementById('loadingWheel').style.display = 'none';
                document.getElementById("recordButton").style.display = "inline-block";
                if (containerContent != '') {
                    container.innerHTML = containerContent;
                    console.log(container.innerHTML);
                }
            });
        });
    });
    

    //function to start recording audio
    let mediaRecorder
    let stopButton = document.getElementById('stopButton');
    const startAgainButtons = document.querySelectorAll('.audioStarter');

    startAgainButtons.forEach(button => {
        //on click of the recordButton (or of the againButton):
        //ask permission for recording the audio
        //record the audio and store it in the file input inside the fileStorage input
        button.addEventListener('click', async () => {
            let audioChunks = [];
            document.getElementById("recordButton").style.display = 'none';
            document.getElementById("againButton").style.display = 'none';
            document.getElementById('audioPlayer').style.display = 'none';

            // Request microphone access
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);

                stopButton.style.display = 'block';
                document.getElementById('recordButton').disabled = true;
                document.getElementById('loadingWheel').style.display = 'block';
                document.getElementById("delButton").style.display = 'none';
                document.getElementById('audioForm').style.display = 'none';
            
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    document.getElementById('audioForm').style.display = 'block';
                    document.getElementById('loadingWheel').style.display = 'none';
                                        
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    var audioPlayer = document.getElementById('audioPlayer');

                    audioPlayer.src = audioUrl;
                    audioPlayer.load();

                    var filename = 'recordedAudio_' + Math.random().toString(36).substr(2, 8) + ".wav";

                    // Create a File object from the Blob
                    const audioFile = new File([audioBlob], filename, { type: 'audio/wav' });

                    // Trigger form file input change event
                    const fileInput = document.getElementById('audioStorage');
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(audioFile);
                    fileInput.files = dataTransfer.files;
                };

                mediaRecorder.start();
                console.log('Recording started');
            } catch (error) {
                console.error('Error accessing microphone:', error);
            }
        });
    });

    stopButton.addEventListener('click', () => {
        stopButton.style.display = 'none';
        document.getElementById("againButton").style.display = 'block';
        document.getElementById("delButton").style.display = 'block';
        document.getElementById('audioPlayer').style.display = 'block';


        if (mediaRecorder) {
            mediaRecorder.stop();
            console.log('Recording stopped');
        }
    });

    var delButton = document.getElementById("delButton");

    delButton.addEventListener('click', () => {
        // Hide the delete button
        delButton.style.display = 'none';

        document.getElementById("againButton").style.display = 'none';
        document.getElementById('audioForm').style.display = 'none';
        document.getElementById("recordButton").style.display = 'inline-block';
        document.getElementById("recordButton").disabled = false; 
        document.getElementById('audioPlayer').style.display = 'none';

        // Clear the audio player source
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = '';
        audioPlayer.load();
    
        // Clear the file input
        const fileInput = document.getElementById('audioStorage');
        fileInput.value = '';  // Clearing the file input value
    });

    //function to display a redirection button to the homepage after 15 minutes of inactivity

    //series of document event listener to detect any touch in the screen, movements with the pointer or pressing any key 
    //this ensure to restart the timer when any of this event is triggered
    document.addEventListener('keydown', (event) => {
        startOrResetInterval();
        console.log("the timeout has been resetted");
    });

    document.addEventListener('touchstart', (event) => {
        startOrResetInterval();
        console.log("the timeout has been resetted");
    });

    document.addEventListener('wheel', (event) => {
        startOrResetInterval();
        console.log("the timeout has been resetted");
    });

    //event to repeat any 15 minutes 
    let intervalId;

    function homepage() {
        console.log("redirecting to the start_chat_page url");
        window.location.replace('/');
    };

    function startOrResetInterval() {
        // Clear the existing interval if it exists
        if (intervalId) {
            clearInterval(intervalId);
        }

        // Set up the new interval
        const interval = 15 * 60 * 1000; // 15 minutes
        intervalId = setInterval(homepage, interval);
    }

    startOrResetInterval();
});


recordButton