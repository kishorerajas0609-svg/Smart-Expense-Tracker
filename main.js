/**
 * Smart Expense Tracker - Frontend Logic & Smart Category Suggestion
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------------------
    // 1. Mobile Sidebar Toggle & Overlay
    // -------------------------------------------------------------------------
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('show');
        });

        sidebarOverlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
        });
    }

    // -------------------------------------------------------------------------
    // 2. Smart Category Keyword Prediction
    // -------------------------------------------------------------------------
    const descInput = document.getElementById('id_description');
    const categorySelect = document.getElementById('id_category');
    const suggestionContainer = document.getElementById('smartSuggestionContainer');

    // Category Keyword Dictionary (Fallback and dynamic match)
    const keywordsMap = {
        'Travel': [
            'uber', 'ola', 'lyft', 'bus', 'train', 'metro', 'flight', 'airline',
            'petrol', 'diesel', 'fuel', 'gas station', 'toll', 'parking', 'taxi',
            'cab', 'transit', 'auto', 'commute', 'railway', 'fare', 'subway'
        ],
        'Food': [
            'pizza', 'burger', 'restaurant', 'cafe', 'coffee', 'groceries',
            'grocery', 'supermarket', 'lunch', 'dinner', 'breakfast', 'meal',
            'snack', 'snacks', 'starbucks', 'mcdonald', 'kfc', 'domino', 'swiggy',
            'zomato', 'foodpanda', 'doordash', 'dining', 'food', 'bakery', 'tea',
            'juice', 'bread', 'milk', 'vegetables', 'fruits', 'diner'
        ],
        'Bills': [
            'electricity', 'water', 'internet', 'wifi', 'phone', 'mobile', 'rent',
            'gas', 'utility', 'utilities', 'bills', 'bill', 'recharge', 'broadband',
            'maintenance', 'landline', 'dth', 'cylinder', 'sewer', 'trash'
        ],
        'Entertainment': [
            'movie', 'cinema', 'games', 'gaming', 'netflix', 'spotify', 'hulu',
            'disney', 'prime video', 'party', 'club', 'concert', 'theater',
            'amusement', 'outing', 'pub', 'entertainment', 'steam', 'playstation',
            'xbox', 'music', 'ticket', 'show', 'bowling'
        ],
        'Healthcare': [
            'doctor', 'medicine', 'pharmacy', 'hospital', 'clinic', 'dental',
            'dentist', 'medical', 'health', 'tablet', 'tablets', 'pills', 'syrup',
            'prescription', 'checkup', 'lab test', 'blood test', 'optical',
            'glasses', 'therapy', 'vaccine', 'physio'
        ],
        'Education': [
            'books', 'book', 'tuition', 'courses', 'course', 'class', 'classes',
            'udemy', 'coursera', 'edx', 'college', 'school', 'fee', 'fees',
            'exam', 'university', 'stationery', 'textbook', 'training', 'tutor',
            'academy', 'seminar', 'workshop'
        ],
        'Shopping': [
            'amazon', 'flipkart', 'clothes', 'clothing', 'shoes', 'dress', 'shirt',
            'shopping', 'mall', 'zara', 'h&m', 'electronics', 'gadget', 'accessory',
            'accessories', 'cosmetics', 'perfume', 'watch', 'boots', 'jacket',
            'myntra', 'ebay', 'walmart', 'target'
        ]
    };

    let userManuallyChangedCategory = false;

    if (categorySelect) {
        categorySelect.addEventListener('change', function () {
            userManuallyChangedCategory = true;
            if (suggestionContainer) {
                suggestionContainer.innerHTML = `
                    <span class="badge bg-secondary">
                        <i class="bi bi-pencil-fill me-1"></i> Manual selection: ${categorySelect.options[categorySelect.selectedIndex].text}
                    </span>
                `;
            }
        });
    }

    if (descInput && categorySelect) {
        descInput.addEventListener('input', function () {
            const text = descInput.value.toLowerCase().trim();
            if (!text) {
                if (suggestionContainer) suggestionContainer.innerHTML = '';
                return;
            }

            let predictedCategory = null;
            let matchedKeyword = null;

            for (const [cat, words] of Object.entries(keywordsMap)) {
                for (const w of words) {
                    // Check if keyword is contained in description
                    if (text.includes(w)) {
                        predictedCategory = cat;
                        matchedKeyword = w;
                        break;
                    }
                }
                if (predictedCategory) break;
            }

            if (predictedCategory) {
                // Select category in dropdown
                categorySelect.value = predictedCategory;

                if (suggestionContainer) {
                    suggestionContainer.innerHTML = `
                        <div class="smart-suggestion-pill">
                            <i class="bi bi-magic"></i>
                            <span>Smart Suggestion: <strong>${predictedCategory}</strong> (matched "${matchedKeyword}")</span>
                            <span class="text-muted ms-1">(You can change it anytime)</span>
                        </div>
                    `;
                }
            } else {
                if (suggestionContainer && !userManuallyChangedCategory) {
                    suggestionContainer.innerHTML = '';
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 3. Preset Date Range Quick Select
    // -------------------------------------------------------------------------
    const timeFilterSelect = document.getElementById('id_time_filter');
    const customDateBox = document.getElementById('customDateInputs');
    if (timeFilterSelect && customDateBox) {
        const toggleCustomDates = () => {
            if (timeFilterSelect.value === 'custom') {
                customDateBox.style.display = 'flex';
            } else {
                customDateBox.style.display = 'none';
            }
        };
        timeFilterSelect.addEventListener('change', toggleCustomDates);
        toggleCustomDates();
    }

    // -------------------------------------------------------------------------
    // 4. Auto-dismiss alerts after 6 seconds
    // -------------------------------------------------------------------------
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 6000);
});
