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
    var songTitle = primarySelectionDropdown.value;
    var songArtist = secondarySelectionDropdown.value;

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

function showSongPreview() {
    
    const storedData = localStorage.getItem('myData');

    if (storedData) {
        const data = JSON.parse(storedData);
        console.log(data);
        primarySelectionDropdown.value = data.title;

        secondarySelectionDropdown.options.length = 0;
        const option = document.createElement('option');
        option.textContent = data.artist;
        option.value = data.artist;
        secondarySelectionDropdown.appendChild(option);

        displaySongData(data);
    }
}

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
