document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const query = document.getElementById('query').value;
            const response = await fetch('/tools/search_rulebook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });
            const data = await response.json();
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            if (data.results) {
                data.results.forEach(result => {
                    const resultDiv = document.createElement('div');
                    resultDiv.innerHTML = `
                        <h2>${result.content_chunk.title}</h2>
                        <p>${result.content_chunk.content}</p>
                        <p><i>Rulebook: ${result.content_chunk.rulebook}, Page: ${result.content_chunk.page_number}</i></p>
                    `;
                    resultsDiv.appendChild(resultDiv);
                });
            }
        });
    }

    const addRulebookForm = document.getElementById('add-rulebook-form');
    if (addRulebookForm) {
        addRulebookForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const pdfPath = document.getElementById('pdf-path').value;
            const rulebookName = document.getElementById('rulebook-name').value;
            const system = document.getElementById('system').value;
            const response = await fetch('/tools/add_rulebook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pdf_path: pdfPath,
                    rulebook_name: rulebookName,
                    system,
                }),
            });
            const data = await response.json();
            alert(data.message);
        });
    }

    const manageCampaignForm = document.getElementById('manage-campaign-form');
    if (manageCampaignForm) {
        manageCampaignForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const campaignId = document.getElementById('campaign-id').value;
            const action = document.getElementById('action').value;
            const dataType = document.getElementById('data-type').value;
            const dataId = document.getElementById('data-id').value;
            const data = document.getElementById('data').value;

            const payload = {
                campaign_id: campaignId,
                action,
                data_type: dataType,
                data_id: dataId,
                data: data ? JSON.parse(data) : null,
            };

            const response = await fetch('/tools/manage_campaign', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const responseData = await response.json();
            const resultsDiv = document.getElementById('campaign-results');
            resultsDiv.innerHTML = '';
            if (responseData.results) {
                responseData.results.forEach(result => {
                    const resultDiv = document.createElement('div');
                    resultDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                    resultsDiv.appendChild(resultDiv);
                });
            } else {
                alert(JSON.stringify(responseData));
            }
        });
    }

    const manageSessionForm = document.getElementById('manage-session-form');
    if (manageSessionForm) {
        manageSessionForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const campaignId = document.getElementById('campaign-id').value;
            const sessionId = document.getElementById('session-id').value;
            const action = document.getElementById('action').value;
            const data = document.getElementById('data').value;

            const payload = {
                campaign_id: campaignId,
                session_id: sessionId,
                action,
                data: data ? JSON.parse(data) : null,
            };

            const response = await fetch('/tools/manage_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const responseData = await response.json();
            const resultsDiv = document.getElementById('session-results');
            resultsDiv.innerHTML = '';
            if (responseData) {
                resultsDiv.innerHTML = `<pre>${JSON.stringify(responseData, null, 2)}</pre>`;
            } else {
                alert(JSON.stringify(responseData));
            }
        });
    }
});
