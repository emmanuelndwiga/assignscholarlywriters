(function() {
    const API = window.ScholarlyAPI;
    let calcData = null;

    // Load dropdowns on page load
    async function init() {
        try {
            const [levels, services, deadlines, currencies] = await Promise.all([
                API.getAcademicLevels(),
                API.getServiceTypes(),
                API.getDeadlines(),
                API.getCurrencies(),
            ]);

            populateSelect('calcLevel', levels, 'name', 'id');
            populateSelect('calcService', services, 'name', 'id');
            populateSelect('calcDeadline', deadlines, 'name', 'id');
            populateSelect('calcCurrency', currencies, 'code', 'code', true);
        } catch (err) {
            console.error('Failed to load calculator data:', err);
            document.querySelectorAll('#calcForm select').forEach(s => {
                s.innerHTML = '<option>Failed to load. Is the backend running?</option>';
            });
        }
    }

    function populateSelect(id, items, labelKey, valueKey, addSymbol) {
        const select = document.getElementById(id);
        select.innerHTML = '<option value="">Select...</option>';
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item[valueKey];
            opt.textContent = addSymbol ? `${item[labelKey]} (${item.symbol || ''})` : item[labelKey];
            select.appendChild(opt);
        });
    }

    // Calculate price
    document.getElementById('calcForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('calcBtn');
        btn.disabled = true;
        btn.textContent = 'Calculating...';

        try {
            const result = await API.calculatePrice({
                service_id: parseInt(document.getElementById('calcService').value),
                academic_level_id: parseInt(document.getElementById('calcLevel').value),
                pages: parseInt(document.getElementById('calcPages').value),
                deadline_id: parseInt(document.getElementById('calcDeadline').value),
                currency_code: document.getElementById('calcCurrency').value,
            });

            if (result.success) {
                calcData = result.data;
                showResult(result.data);
            } else {
                alert('Calculation failed. Please check your inputs.');
            }
        } catch (err) {
            console.error(err);
            alert('Could not connect to the backend. Please ensure the server is running.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<svg style="width:18px;height:18px;vertical-align:middle;margin-right:6px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Calculate Price';
        }
    });

    function showResult(data) {
        const resultEl = document.getElementById('calcResult');
        const priceEl = document.getElementById('resultPrice');
        const detailsEl = document.getElementById('resultDetails');

        priceEl.textContent = `${data.currency_symbol}${data.final_price} ${data.target_currency}`;

        detailsEl.innerHTML = `
            <div class="calc-detail-row"><span>Base Price (${data.base_currency})</span><span>${data.currency_symbol}${data.base_price}</span></div>
            <div class="calc-detail-row"><span>Academic Level</span><span>x${data.level_multiplier}</span></div>
            <div class="calc-detail-row"><span>Deadline</span><span>x${data.deadline_multiplier}</span></div>
            <div class="calc-detail-row"><span>Pricing Season</span><span>${data.pricing_season} (x${data.season_multiplier})</span></div>
            ${data.target_currency !== data.base_currency ? `<div class="calc-detail-row"><span>Exchange Rate</span><span>1 ${data.base_currency} = ${data.exchange_rate} ${data.target_currency}</span></div>` : ''}
            <div class="calc-detail-row"><span>Total Words</span><span>${data.total_words}</span></div>
        `;

        resultEl.style.display = 'block';
        document.getElementById('enquirySection').style.display = 'block';
        resultEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Submit enquiry
    document.getElementById('enquiryForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('eqSubmitBtn');
        btn.disabled = true;
        btn.textContent = 'Submitting...';

        const formData = new FormData();
        formData.append('customer_name', document.getElementById('eqName').value);
        formData.append('customer_email', document.getElementById('eqEmail').value);
        formData.append('customer_phone', document.getElementById('eqPhone').value);
        formData.append('customer_whatsapp', document.getElementById('eqWhatsapp').value);
        formData.append('service_id', document.getElementById('calcService').value);
        formData.append('academic_level_id', document.getElementById('calcLevel').value);
        formData.append('pages', document.getElementById('calcPages').value);
        formData.append('deadline_id', document.getElementById('calcDeadline').value);
        formData.append('currency_code', document.getElementById('calcCurrency').value);
        formData.append('course_subject', document.getElementById('eqCourse').value);
        formData.append('specifications', document.getElementById('eqSpecs').value);

        const files = document.getElementById('eqFiles').files;
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const result = await API.submitQuotation(formData);
            if (result.success) {
                document.getElementById('enquiryForm').style.display = 'none';
                document.getElementById('eqRequestId').textContent = 'Q-' + result.quotation.request_id;
                document.getElementById('eqSuccess').style.display = 'block';
                document.getElementById('eqSuccess').scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                alert('Submission failed. Please try again.');
            }
        } catch (err) {
            console.error(err);
            alert('Could not connect to the backend. Please ensure the server is running.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Submit Enquiry';
        }
    });

    // Smooth scroll to calculator from pricing cards
    document.querySelectorAll('.pricing-card .btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.getAttribute('href') === '#calcForm') {
                e.preventDefault();
                document.getElementById('calcForm').scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    });

    init();
})();
