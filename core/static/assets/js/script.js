const imgs = document.querySelectorAll('.header-slider ul img');
const prev_btn = document.querySelector('.prev');
const next_btn = document.querySelector('.next');

let n = 0;

function changeslide() {
    for (let i = 0; i < imgs.length; i++) {
        imgs[i].style.display = 'none';
    }
    imgs[n].style.display = 'block';
}
changeslide();

prev_btn.addEventListener('click', (e) => { 
    if (n > 0) {
        n--;  
    } else {
        n = imgs.length - 1;
    }
    changeslide();
});
next_btn.addEventListener('click', (e) => { 
    if (n < imgs.length - 1) {
        n++;  
    } else {
        n = 0;
    }
    changeslide();
})


const productSlider = document.querySelector('.products-slider .products');
const productImgs = productSlider.querySelectorAll('img');
let scrollAmount = 0;

function scrollProducts(direction) {
    const scrollStep = productImgs[0].clientWidth + 10; // Assuming 10px margin
    if (direction === 'next') {
        scrollAmount += scrollStep;
        if (scrollAmount >= productSlider.scrollWidth - productSlider.clientWidth) {
            scrollAmount = 0;
        }
    } else {
        scrollAmount -= scrollStep;
        if (scrollAmount < 0) {
            scrollAmount = productSlider.scrollWidth - productSlider.clientWidth;
        }
    }
    productSlider.scrollTo({
        left: scrollAmount,
        behavior: 'smooth'
    });
}

next_btn.addEventListener('click', () => scrollProducts('next'));
prev_btn.addEventListener('click', () => scrollProducts('prev'));




// Wait for the HTML document to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', function() {

    // Find the microphone button element by its class
    const micButton = document.querySelector('.micButton');

    // Check if the button element actually exists on the page
    if (micButton) {
        // Add an event listener that triggers when the button is clicked
        micButton.addEventListener('click', function() {
            // --- Action to perform on click ---

            console.log('Mic button clicked!'); // Log a message to the browser console

            // Display a simple alert message (placeholder for real functionality)
            alert('Voice search feature is not implemented yet.');

            // --- Future Implementation (Web Speech API) ---
            // You would replace the alert above with code like this:
            // 1. Check if the browser supports SpeechRecognition
            // 2. Create a new SpeechRecognition instance
            // 3. Set language and other options
            // 4. Define what happens when speech is recognized (onresult)
            // 5. Define error handling (onerror)
            // 6. Start the recognition process (recognition.start())
            // Example (very basic structure):
            /*
            if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-US'; // Set language

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    console.log('Voice input:', transcript);
                    // Maybe put the transcript into the search input field:
                    // const searchInput = document.querySelector('.input');
                    // if (searchInput) { searchInput.value = transcript; }
                }

                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    alert('Sorry, voice recognition failed: ' + event.error);
                }

                recognition.start(); // Start listening
                console.log('Listening for voice input...');

            } else {
                alert('Sorry, your browser does not support voice recognition.');
            }
            */
        });
    } else {
        // Log a message if the button wasn't found (useful for debugging)
        console.log('Mic button element not found on this page.');
    }

}); // End of DOMContentLoaded listener
