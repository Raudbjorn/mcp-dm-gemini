document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const query = document.getElementById('query').value;
            const rulebook = document.getElementById('rulebook')?.value || null;
            const contentType = document.getElementById('content-type')?.value || null;
            const maxResults = parseInt(document.getElementById('max-results')?.value) || 5;
            const useHybrid = document.getElementById('use-hybrid')?.checked !== false;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<p>Searching...</p>';
            
            try {
                const response = await fetch('/ui/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        query, 
                        rulebook, 
                        content_type: contentType, 
                        max_results: maxResults,
                        use_hybrid: useHybrid
                    }),
                });
                
                if (!response.ok) {
                    throw new Error('Search failed');
                }
                
                const data = await response.json();
                resultsDiv.innerHTML = '';
                
                // Show search statistics
                if (data.search_stats) {
                    const statsDiv = document.createElement('div');
                    statsDiv.className = 'search-stats';
                    statsDiv.innerHTML = `
                        <p><strong>Found ${data.search_stats.total_results} results</strong> 
                        (${data.search_stats.search_type} search${data.search_stats.personality_enhanced ? ', personality-enhanced' : ''})</p>
                    `;
                    resultsDiv.appendChild(statsDiv);
                }
                
                // Show personality context if available
                if (data.personality_context) {
                    const personalityDiv = document.createElement('div');
                    personalityDiv.className = 'personality-context';
                    personalityDiv.innerHTML = `
                        <div class="personality-banner">
                            <strong>🎭 ${data.personality_context.personality_name}</strong> 
                            (${data.personality_context.system_name} - ${data.personality_context.tone} tone)
                        </div>
                    `;
                    resultsDiv.appendChild(personalityDiv);
                }
                
                // Show suggestions if available
                if (data.suggestions && data.suggestions.length > 0) {
                    const suggestionsDiv = document.createElement('div');
                    suggestionsDiv.className = 'suggestions';
                    suggestionsDiv.innerHTML = '<h3>💡 Search Suggestions:</h3>';
                    data.suggestions.forEach(suggestion => {
                        const suggestionDiv = document.createElement('div');
                        suggestionDiv.className = 'suggestion';
                        suggestionDiv.innerHTML = `
                            <p><strong>${suggestion.suggestion_type}:</strong> 
                            <a href="#" onclick="searchWithSuggestion('${suggestion.suggested_query}')">${suggestion.suggested_query}</a>
                            <span class="confidence">(${(suggestion.confidence * 100).toFixed(0)}% confidence)</span></p>
                            <p><em>${suggestion.explanation}</em></p>
                        `;
                        suggestionsDiv.appendChild(suggestionDiv);
                    });
                    resultsDiv.appendChild(suggestionsDiv);
                }
                
                // Show results
                if (data.results && data.results.length > 0) {
                    data.results.forEach((result, index) => {
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'search-result';
                        resultDiv.innerHTML = `
                            <div class="result-header">
                                <h3>${result.content_chunk.title}</h3>
                                <span class="relevance-score">${(result.relevance_score * 100).toFixed(0)}% relevant</span>
                            </div>
                            <div class="result-content">
                                <p>${result.content_chunk.content.substring(0, 500)}${result.content_chunk.content.length > 500 ? '...' : ''}</p>
                            </div>
                            <div class="result-meta">
                                <span class="rulebook">📚 ${result.content_chunk.rulebook}</span>
                                <span class="page">📄 Page ${result.content_chunk.page_number}</span>
                                <span class="system">🎲 ${result.content_chunk.system}</span>
                                <span class="type">🏷️ ${result.content_chunk.content_type}</span>
                                <span class="match-type">🔍 ${result.match_type}</span>
                            </div>
                        `;
                        resultsDiv.appendChild(resultDiv);
                    });
                } else if (!data.suggestions || data.suggestions.length === 0) {
                    resultsDiv.innerHTML += '<p>No results found. Try different search terms or check that you have added rulebooks.</p>';
                }
            } catch (error) {
                resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            }
        });
    }
    
    // Helper function for suggestion clicks
    window.searchWithSuggestion = function(suggestedQuery) {
        document.getElementById('query').value = suggestedQuery;
        document.getElementById('search-form').dispatchEvent(new Event('submit'));
    };
}

    const addRulebookForm = document.getElementById('add-rulebook-form');
    if (addRulebookForm) {
        addRulebookForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const pdfPath = document.getElementById('pdf-path').value;
            const rulebookName = document.getElementById('rulebook-name').value;
            const system = document.getElementById('system').value;
            
            const submitButton = event.target.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Processing... (this may take several minutes)';
            submitButton.disabled = true;
            
            try {
                const response = await fetch('/ui/api/add-rulebook', {
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
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to add rulebook');
                }
                
                const data = await response.json();
                
                const resultsDiv = document.getElementById('add-results') || createResultsDiv();
                resultsDiv.innerHTML = `
                    <div class="success-message">
                        <h3>✅ Success!</h3>
                        <p>${data.message}</p>
                    </div>
                `;
                
                // Clear the form
                addRulebookForm.reset();
                
            } catch (error) {
                const resultsDiv = document.getElementById('add-results') || createResultsDiv();
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <h3>❌ Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            } finally {
                submitButton.textContent = originalText;
                submitButton.disabled = false;
            }
        });
        
        function createResultsDiv() {
            const resultsDiv = document.createElement('div');
            resultsDiv.id = 'add-results';
            addRulebookForm.parentNode.insertBefore(resultsDiv, addRulebookForm.nextSibling);
            return resultsDiv;
        }
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
