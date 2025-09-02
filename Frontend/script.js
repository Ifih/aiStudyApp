document.addEventListener('DOMContentLoaded', () => {
            const notesInput = document.getElementById('notesInput');
            const generateButton = document.getElementById('generateButton');
            const flashcardContainer = document.getElementById('flashcardContainer');
            const messageBox = document.getElementById('messageBox');
            const messageText = document.getElementById('messageText');
            const closeMessageBox = document.getElementById('closeMessageBox');

            // Function to show a custom message box
            function showMessage(text) {
                messageText.textContent = text;
                messageBox.style.display = 'block';
            }

            // Function to close the custom message box
            closeMessageBox.onclick = () => {
                messageBox.style.display = 'none';
            };

            generateButton.addEventListener('click', async () => {
                const notes = notesInput.value.trim();
                if (notes === '') {
                    showMessage('Please enter some notes to generate flashcards.');
                    return;
                }

                // Show a loading state
                flashcardContainer.innerHTML = '<p>Generating flashcards... please wait.</p>';

                try {
                    const response = await fetch('http://localhost:5000/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ notes: notes })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to generate flashcards. Please try again.');
                    }

                    const data = await response.json();
                    
                    if (data.flashcards && data.flashcards.length > 0) {
                        renderFlashcards(data.flashcards);
                    } else {
                        flashcardContainer.innerHTML = '<p>No flashcards were generated. Please provide more detailed notes.</p>';
                    }

                } catch (error) {
                    console.error('Error:', error);
                    flashcardContainer.innerHTML = '<p>Error generating flashcards. The backend server may not be running.</p>';
                }
            });

            function renderFlashcards(flashcards) {
                flashcardContainer.innerHTML = ''; // Clear previous cards
                flashcards.forEach(card => {
                    const flashcardEl = document.createElement('div');
                    flashcardEl.className = 'flashcard';
                    flashcardEl.innerHTML = `
                        <div class="flashcard-inner">
                            <div class="flashcard-front">
                                <p>${card.question}</p>
                            </div>
                            <div class="flashcard-back">
                                <p>${card.answer}</p>
                            </div>
                        </div>
                    `;
                    flashcardEl.addEventListener('click', () => {
                        flashcardEl.classList.toggle('flipped');
                    });
                    flashcardContainer.appendChild(flashcardEl);
                });
            }
        });