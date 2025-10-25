const songDropdownGroup = document.getElementById('songDropdownGroup');
const primarySelectionDropdown = document.getElementById('primarySelectionDropdown');
const primarySelectionListOverlay = document.getElementById('primarySelectionListOverlay');
const primarySelectionList = document.getElementById('primarySelectionList');
const secondarySelectionDropdown = document.getElementById('secondarySelectionDropdown');
const noSongsMessageP = document.getElementById('noSongsMessage');
const selectionSwitch = document.getElementById('selectionSwitch');
const selectionSwitchLabel = document.getElementById('selectionSwitchLabel');
const songSelectorGroup = document.getElementById('songSelect');
const artistSelectorGroup = document.getElementById('artistSelect');
const selectionLabel1 = document.getElementById('selection-label1');
const selectionLabel2 = document.getElementById('selection-label2');

// Song details elements
const songDetailsContainer = document.getElementById('songDetailsContainer');
const songTitleArtistEl = document.getElementById('songTitleArtist');
const songChordsUl = document.getElementById('songChords');
const songLyricsPre = document.getElementById('songLyrics');
const errorMessageDiv = document.getElementById('errorMessage');

// Scroll Control Elements (MODIFIED: Removed resetScrollButton)
const toggleScrollButton = document.getElementById('startScrollButton'); // This button will now toggle start/stop
// const resetScrollButton = document.getElementById('resetScrollButton'); // REMOVED
const scrollSpeedInput = document.getElementById('scrollSpeed');
const scrollSpeedValueSpan = document.getElementById('scrollSpeedValue');

// Font Size Control Element
const decreaseFontSizeButton = document.getElementById('decreaseFontSize');
const increaseFontSizeButton = document.getElementById('increaseFontSize');

// Global state variables
let scrollInterval = null;
let currentScrollSpeed = 1; // Default, will be updated by input
const SCROLL_INTERVAL_MS = 300; // Base interval for scroll updates
let selectedFiles = [];

// Define font size steps
let currentFontSizeEm = 1.5; // Initial font size for #songLyrics, matches medium
const FONT_SIZE_STEP = 0.1; // How much to increase/decrease by
const MIN_FONT_SIZE_EM = 1.0;
const MAX_FONT_SIZE_EM = 3.0;

// --- Font Size Control Function ---
/**
 * Applies the selected font size to the song lyrics.
 */
function applyFontSize() {
    if (!songLyricsPre) {
        console.error("Error: songLyricsPre element not found when applying font size!");
        return;
    }
    songLyricsPre.style.fontSize = `${currentFontSizeEm}em`;
}

/**
 * Increases the font size and applies it.
 */
function increaseFontSize() {
    if (currentFontSizeEm < MAX_FONT_SIZE_EM) {
        currentFontSizeEm += FONT_SIZE_STEP;
        applyFontSize();
    }
}

/**
 * Decreases the font size and applies it.
 */
function decreaseFontSize() {
    if (currentFontSizeEm > MIN_FONT_SIZE_EM) {
        currentFontSizeEm -= FONT_SIZE_STEP;
        applyFontSize();
    }
}

// --- Scroll Control Functions (ADAPTED for single toggle button) ---

/**
 * Starts the automatic scrolling of the lyrics (internal logic).
 * Does NOT handle button state directly, that's for toggleScroll().
 */
function startLyricsScrollInternal() {
    if (!songLyricsPre || scrollInterval) {
        return; // Don't start if element is missing or already scrolling
    }

    // If lyrics are not tall enough to scroll, don't start
    if (songLyricsPre.scrollHeight <= songLyricsPre.clientHeight) {
        // Since we can't scroll, ensure button state reflects "Start"
        toggleScrollButton.textContent = 'Start Scroll';
        // resetScrollButton.disabled = false; // REMOVED
        return;
    }

    scrollInterval = setInterval(() => {
        songLyricsPre.scrollTop += currentScrollSpeed;
        if (songLyricsPre.scrollTop + songLyricsPre.clientHeight >= songLyricsPre.scrollHeight - 1) {
            // Reached bottom, stop scrolling and reset button state
            stopLyricsScrollInternal(); // Stop the interval
            toggleScrollButton.textContent = 'Start Scroll'; // Update button text
            // resetScrollButton.disabled = false; // REMOVED
            // Optional: Reset scroll position to top after reaching end,
            // or leave it at the end to allow manual scrolling back up.
            // If you want it to jump to top: songLyricsPre.scrollTop = 0;
        }
    }, SCROLL_INTERVAL_MS);
}

/**
 * Stops the automatic scrolling of the lyrics (internal logic).
 * Does NOT handle button state directly, that's for toggleScroll().
 */
function stopLyricsScrollInternal() {
    if (scrollInterval) {
        clearInterval(scrollInterval);
        scrollInterval = null;
    }
}

/**
 * Toggles the scroll state (start/stop) and updates the button text accordingly.
 * This is the function attached to the single "Start Scroll" button.
 */
function toggleScroll() {
    if (scrollInterval) { // If currently scrolling
        stopLyricsScrollInternal();
        toggleScrollButton.textContent = 'Start Scroll';
        // resetScrollButton.disabled = false; // REMOVED
    } else { // If not scrolling
        startLyricsScrollInternal(); // Attempt to start scrolling
        // Only change button text to 'Stop Scroll' if scrolling actually started
        if (scrollInterval) {
            toggleScrollButton.textContent = 'Stop Scroll';
            // resetScrollButton.disabled = true; // REMOVED
        }
    }
}

/**
 * Updates the scroll speed. If already scrolling, restarts with new speed.
 */
function updateScrollSpeed() {
    currentScrollSpeed = parseInt(scrollSpeedInput.value) || 1;
    scrollSpeedValueSpan.textContent = currentScrollSpeed;

    // If already scrolling, restart with the new speed
    if (scrollInterval) {
        stopLyricsScrollInternal(); // Clear existing interval
        startLyricsScrollInternal(); // Start new one with updated speed
        // Button state should remain 'Stop Scroll'
        toggleScrollButton.textContent = 'Stop Scroll';
        // resetScrollButton.disabled = true; // REMOVED
    }
}
// --- END: Initialize and Update Speed ---

// Display Song Data
function displaySongData(songData) {
    // When a new song is loaded, automatically reset scroll position and button state
    stopLyricsScrollInternal(); // Ensure any ongoing scroll is stopped
    if (songLyricsPre) {
        songLyricsPre.scrollTop = 0; // Reset lyrics to the top
    }
    toggleScrollButton.textContent = 'Start Scroll'; // Set button to 'Start Scroll'

    errorMessageDiv.textContent = '';
    songChordsUl.innerHTML = '';

    const title = songData.title || "";
    const artist = songData.artist || "";

    if (title === "N/A" && artist === "N/A") {
        songTitleArtistEl.textContent = "Song Details N/A"; // Or just ""
    } else if (artist === "N/A") {
        songTitleArtistEl.textContent = title; // Only title if artist is N/A
    } else if (title === "N/A") {
        songTitleArtistEl.textContent = artist; // Only artist if title is N/A (or maybe "Unknown Title - Artist")
                                                // Let's stick to the "Title - Artist" format more strictly
        songTitleArtistEl.textContent = `N/A - ${artist}`;
    }
    else {
        songTitleArtistEl.textContent = `${title} - ${artist}`;
    }
    // --- END OF MODIFICATION ---

    if (songData.chords && Array.isArray(songData.chords)) {
        if (songData.chords.length > 0) {
            songData.chords.forEach(chord => {
                const li = document.createElement('li');
                const img = document.createElement('img');
                img.src = `chords/${encodeURIComponent(chord)}.png`;
                img.alt = `${chord} chord diagram`;
                img.classList.add('chord-image');
                img.onerror = function() {
                    li.innerHTML = '';
                    const fallbackText = document.createElement('span');
                    fallbackText.textContent = chord;
                    fallbackText.classList.add('chord-image-missing');
                    li.appendChild(fallbackText);
                };
                li.appendChild(img);
                songChordsUl.appendChild(li);
            });
        } else {
             const li = document.createElement('li');
             li.textContent = "No chords listed.";
             songChordsUl.appendChild(li);
        }
    } else {
        const li = document.createElement('li');
        li.textContent = "Chords N/A";
        songChordsUl.appendChild(li);
    }

    let lyricsText = songData.lyrics || "No lyrics provided.";
    if (lyricsText !== "No lyrics provided.") {
        const highlightRegex = /(\[.*?\]|\(.*?\))/g;
        //const formattedLyrics = lyricsText.replace(highlightRegex, '<b>$&</b>');
        const formattedLyrics = lyricsText.replace(highlightRegex, '<b>$&</b>') + "\n\n\n\n\n\n\n\n";
        songLyricsPre.innerHTML = formattedLyrics;
    } else {
        songLyricsPre.textContent = lyricsText;
    }
    songDetailsContainer.style.display = 'block';

    applyFontSize(); // Apply font size after loading new song data
}


function clearPrimarySelectionList() {
    var li = primarySelectionList.getElementsByTagName("li");

    console.log("Clearing Selection List...");

    for (i = 0; i < li.length; i++) {
        li[i].style.display = "none";
    }

}

function processKeyInput() {
    var filter = primarySelectionDropdown.value.toUpperCase();

    if(filter.length == 0) {

        clearPrimarySelectionList();

    } else {

        var li = primarySelectionList.getElementsByTagName("li");

        for (i = 0, liCtr = 0; i < li.length && liCtr < 15; i++) {
            var a = li[i].getElementsByTagName("a")[0];
            var txtValue = a.textContent || a.innerText;
            if ((txtValue.toUpperCase().indexOf(filter) > -1)) {
                console.log("Displaying: ", txtValue);
                li[i].style.display = "";
                liCtr++;
            } else {
                console.log("Hiding: ", txtValue);
                li[i].style.display = "none";
            }
        }
    }

    console.log("Key Press Detected!");
}

// Song Dropdown Change Listener
function handleSongChangeEvent(event) {

    const songTitle = event.target.textContent;

    if (event.target.closest('li')) {
        primarySelectionDropdown.removeEventListener('keyup', processKeyInput);
        primarySelectionDropdown.value = songTitle;
        clearPrimarySelectionList();
        primarySelectionDropdown.addEventListener('keyup', processKeyInput);
        console.log("Target Matches!");
    } 

    const xhr = new XMLHttpRequest();
    const httpQuery = "http://localhost:3001/listDistinctArtists?title=" + songTitle;
    xhr.open('GET', httpQuery); // Replace with your API endpoint

    secondarySelectionDropdown.options.length = 1;

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log(data);
  
            data.forEach((artist, index) => {
        
                console.log("Adding: <" + artist + "> to Artist Dropdown Box");
        
                const option = document.createElement('option');
                option.textContent = artist;
                option.value = artist;
                secondarySelectionDropdown.appendChild(option);
            });
    
            if(secondarySelectionDropdown.options.length == 2){
                secondarySelectionDropdown.selectedIndex = 1;
            }

        } else {
            console.error("Request failed. Status:", xhr.status);
        }
    };
    xhr.onerror = function() {
        console.error("Request failed");
    };

    xhr.send();

}

function handleArtistChangeEvent(event) {

    const artist = event.target.textContent;

    if (event.target.closest('li')) {
        primarySelectionDropdown.removeEventListener('keyup', processKeyInput);
        primarySelectionDropdown.value = artist;
        clearPrimarySelectionList();
        primarySelectionDropdown.addEventListener('keyup', processKeyInput);
        console.log("Target Matches!");
    }

    const xhr = new XMLHttpRequest();
    const httpQuery = "http://localhost:3001/listDistinctTitles?artist=" + artist;
    xhr.open('GET', httpQuery); // Replace with your API endpoint

    secondarySelectionDropdown.options.length = 1;

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log(data);

            data.forEach((song, index) => {

                console.log("Adding: <" + song + "> to Title Dropdown Box");

                const option = document.createElement('option');
                option.textContent = song;
                option.value = song;
                secondarySelectionDropdown.appendChild(option);
            });

            if(secondarySelectionDropdown.options.length == 2){
                secondarySelectionDropdown.selectedIndex = 1;
            }

        } else {
            console.error("Request failed. Status:", xhr.status);
        }
    };
    xhr.onerror = function() {
        console.error("Request failed");
    };

    xhr.send();

}

// --- START: Toggle Button event handler ---
function toggleSelection(){
    primarySelectionDropdown.value = "";
    primarySelectionList.replaceChildren();
    secondarySelectionDropdown.options.length = 0;

    const selectSong = document.createElement('option');
    selectSong.textContent = "-- Select a Song --";
    selectSong.value = "-- Select a Song --";

    const selectArtist = document.createElement('option');
    selectArtist.textContent = "-- Select Artist --";
    selectArtist.value = "-- Select Artist --";

    if(selectionSwitch.checked == true) {
        
        console.log("Toggled!");
        selectionSwitchLabel.style.color = "black";
        selectionLabel1.textContent = "Artist:";
        selectionLabel2.textContent = "Title:";
        secondarySelectionDropdown.appendChild(selectSong);
        primarySelectionList.removeEventListener('click', handleSongChangeEvent);
        primarySelectionDropdown.placeholder = "Type in artist...";
        initArtistSelection();

    } else {

        console.log("Not Toggled!");
        selectionSwitchLabel.style.color = "lightgray";
        selectionLabel1.textContent = "Title:";
        selectionLabel2.textContent = "Artist:";
        secondarySelectionDropdown.appendChild(selectArtist);
        primarySelectionList.removeEventListener('click', handleArtistChangeEvent);
        primarySelectionDropdown.placeholder = "Type in song title...";
        initSongSelection();
    }

}
// --- END: Toggle Button event handler ---

// --- START: Go Button event handler ---
function retrieveAndDisplaySong(){
    var songTitle;
    var songArtist;
    
    if(selectionSwitch.checked == true){
        songTitle = secondarySelectionDropdown.value;
        songArtist = primarySelectionDropdown.value;
    } else {
        songTitle = primarySelectionDropdown.value;
        songArtist = secondarySelectionDropdown.value;
    }

    const xhr = new XMLHttpRequest();
    const httpQuery = "http://localhost:3001/getLyrics?artist=" + songArtist + "&title=" + songTitle;
    xhr.open('GET', httpQuery); // Replace with your API endpoint


    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log(data);

            displaySongData(data);

        } else {
            console.error("Request failed. Status:", xhr.status);
        }
    };
    xhr.onerror = function() {
        console.error("Request failed");
    };

    xhr.send();
}
// --- END: Event Listener for Go Button ---

// --- START: Retrieve Songs List via REST API ---
function initSongSelection() {
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', 'http://localhost:3001/listTitles'); // Replace with your API endpoint

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log(data);

            data.forEach((song, index) => {

                //console.log("Adding: <" + song + "> to Title List");

                var primaryLi = document.createElement('li');
                var a = document.createElement('a');
                a.href = "#";
                a.textContent = song;
                primaryLi.appendChild(a);
                primaryLi.style.display = "none";
                primarySelectionList.appendChild(primaryLi);
            });

            primarySelectionList.addEventListener('click', handleSongChangeEvent);

        } else {
            console.error("Request failed. Status:", xhr.status);
        }
    };
    xhr.onerror = function() {
        console.error("Request failed");
    };

    xhr.send();
}
// --- END: Retrieve Songs List via REST API ---

// --- START: Retrieve Artist List via REST API ---
function initArtistSelection() {
   
    const xhr = new XMLHttpRequest();
    xhr.open('GET', 'http://localhost:3001/listArtists'); // Replace with your API endpoint

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log(data);

            data.forEach((artist, index) => {

                //console.log("Adding: <" + artist + "> to Title Dropdown Box");

                var primaryLi = document.createElement('li');
                var a = document.createElement('a');
                a.href = "#";
                a.textContent = artist;
                primaryLi.appendChild(a);
                primaryLi.style.display = "none";
                primarySelectionList.appendChild(primaryLi);
            });

            primarySelectionList.addEventListener('click', handleArtistChangeEvent);

        } else {
            console.error("Request failed. Status:", xhr.status);
        }
    };
    xhr.onerror = function() {
        console.error("Request failed");
    };

    xhr.send();
}
// --- END: Retrieve Artist List via REST API ---

// Attach scroll control event listeners (MODIFIED)
if (toggleScrollButton && scrollSpeedInput && scrollSpeedValueSpan) { // REMOVED: resetScrollButton from check
    toggleScrollButton.addEventListener('click', toggleScroll); 
    // REMOVED: resetScrollButton.addEventListener('click', resetLyricsScroll);
        
    // Initialize speed display and value
    currentScrollSpeed = parseInt(scrollSpeedInput.value) || 1;
    scrollSpeedValueSpan.textContent = currentScrollSpeed;
    
    // Listen for input events on the slider to update speed
    scrollSpeedInput.addEventListener('input', updateScrollSpeed);
} else {
    console.error("One or more essential scroll control elements not found. Check your HTML IDs.");
}
    
// Font Size Event Listener (MODIFIED)
if (decreaseFontSizeButton && increaseFontSizeButton) {
    applyFontSize(); // Apply initial font size
    decreaseFontSizeButton.addEventListener('click', decreaseFontSize);
    increaseFontSizeButton.addEventListener('click', increaseFontSize);
} else {
    console.error("Font size control buttons not found. Check your HTML IDs.");
}

// --- END: Event Listeners for Scroll Controls ---
