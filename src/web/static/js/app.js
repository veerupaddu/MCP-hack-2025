document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const questionInput = document.getElementById('questionInput');
    const submitBtn = document.getElementById('submitBtn');
    const answerSection = document.getElementById('answerSection');
    const answerContent = document.getElementById('answerContent');
    const answerMeta = document.getElementById('answerMeta');
    const sourcesSection = document.getElementById('sourcesSection');
    const sourcesList = document.getElementById('sourcesList');
    const errorSection = document.getElementById('errorSection');
    const errorContent = document.getElementById('errorContent');
    const cancelBtn = document.getElementById('cancelBtn');
    let abortController = null;

    // Cancel button handler
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (abortController) {
                abortController.abort();
                abortController = null;
            }
        });
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;

        // Hide previous results
        answerSection.style.display = 'none';
        errorSection.style.display = 'none';
        sourcesSection.style.display = 'none';

        // Show loading state
        submitBtn.disabled = true;
        if (cancelBtn) cancelBtn.style.display = 'block';
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';
        
        // Show progress message
        let progressMsg = document.getElementById('progressMsg');
        if (!progressMsg) {
            progressMsg = document.createElement('div');
            progressMsg.id = 'progressMsg';
            progressMsg.style.cssText = 'text-align: center; padding: 10px; color: #667eea; font-style: italic;';
            form.parentNode.insertBefore(progressMsg, form.nextSibling);
        }
        progressMsg.textContent = '⏳ Querying RAG system... This may take 10-30 seconds (first query is slower)';

        try {
            // Add timeout to fetch request (2 minutes)
            abortController = new AbortController();
            const timeoutId = setTimeout(() => abortController.abort(), 120000); // 2 minutes
            
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
                signal: abortController.signal
            });
            
            clearTimeout(timeoutId);
            abortController = null; // Clear after successful request

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove progress message
            const progressMsg = document.getElementById('progressMsg');
            if (progressMsg) progressMsg.remove();
            
            // Reset button and cancel button
            submitBtn.disabled = false;
            if (cancelBtn) cancelBtn.style.display = 'none';
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';

            if (data.success) {
                // Show answer with better formatting
                let answerText = data.answer;
                
                // First, escape HTML to prevent XSS, then we'll add our formatting
                const div = document.createElement('div');
                div.textContent = answerText;
                answerText = div.innerHTML;
                
                // Convert markdown-style formatting to HTML
                // Convert **bold** to <strong>
                answerText = answerText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                // Convert *italic* to <em> (but not if it's part of **bold**)
                answerText = answerText.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
                
                // Convert numbered lists (1. 2. 3. etc.)
                const numberedListRegex = /(\d+\.\s+.+(\n\d+\.\s+.+)*)/g;
                answerText = answerText.replace(numberedListRegex, (match) => {
                    const items = match.split(/\n(?=\d+\.)/).map(item => {
                        const text = item.replace(/^\d+\.\s+/, '').trim();
                        return `<li>${text}</li>`;
                    }).join('');
                    return `<ol>${items}</ol>`;
                });
                
                // Convert bullet points (- or •)
                const bulletListRegex = /^[-•]\s+(.+)$/gm;
                if (bulletListRegex.test(answerText)) {
                    answerText = answerText.replace(bulletListRegex, '<li>$1</li>');
                    // Wrap consecutive <li> in <ul>
                    answerText = answerText.replace(/(<li>.*?<\/li>\s*)+/g, (match) => {
                        if (!match.includes('<ol>')) {
                            return '<ul>' + match + '</ul>';
                        }
                        return match;
                    });
                }
                
                // Convert line breaks to paragraphs (but preserve lists)
                const hasLists = answerText.includes('<li>') || answerText.includes('<ol>') || answerText.includes('<ul>');
                
                if (!hasLists) {
                    // Split by double newlines for paragraphs
                    answerText = answerText.split(/\n\n+/).map(p => {
                        p = p.trim();
                        if (!p) return '';
                        // Don't wrap if already HTML tag
                        if (p.match(/^<[^>]+>.*<\/[^>]+>$/)) return p;
                        return '<p>' + p + '</p>';
                    }).join('');
                } else {
                    // For content with lists, convert single newlines to <br> but preserve list structure
                    answerText = answerText.replace(/\n/g, '<br>');
                    // Fix: remove <br> tags that are inside list items
                    answerText = answerText.replace(/(<li>.*?)<br>(.*?<\/li>)/g, '$1 $2');
                    // Remove <br> before/after list tags
                    answerText = answerText.replace(/<br>\s*(<\/?(?:ul|ol|li)>)/g, '$1');
                    answerText = answerText.replace(/(<\/?(?:ul|ol|li)>)\s*<br>/g, '$1');
                }
                
                // Set as HTML
                answerContent.innerHTML = answerText;
                
                // Show metadata
                let metaText = '';
                if (data.retrieval_time) {
                    metaText += `⏱️ Retrieval: ${data.retrieval_time.toFixed(2)}s`;
                }
                if (data.generation_time) {
                    if (metaText) metaText += ' | ';
                    metaText += `Generation: ${data.generation_time.toFixed(2)}s`;
                }
                answerMeta.textContent = metaText;

                // Show sources
                if (data.sources && data.sources.length > 0) {
                    sourcesList.innerHTML = '';
                    data.sources.forEach((source, index) => {
                        const sourceDiv = document.createElement('div');
                        sourceDiv.className = 'source-item';
                        
                        const pathDiv = document.createElement('div');
                        pathDiv.className = 'source-path';
                        pathDiv.textContent = `${index + 1}. ${source.path || 'Source ' + (index + 1)}`;
                        
                        const contentDiv = document.createElement('div');
                        contentDiv.className = 'source-content';
                        let content = (source.content || '').trim();
                        // Clean up markdown table syntax from source content
                        content = content.replace(/\|[\s\-:]+\|/g, '');
                        content = content.replace(/^\|.*\|$/gm, ''); // Remove table rows
                        content = content.replace(/\s+\|\s+/g, ' ');
                        content = content.replace(/\n{3,}/g, '\n\n'); // Clean up excessive newlines
                        // Show more content (increased from 300 to 500)
                        if (content.length > 500) {
                            content = content.substring(0, 500) + '...';
                        }
                        contentDiv.textContent = content || 'Content preview not available';
                        
                        sourceDiv.appendChild(pathDiv);
                        sourceDiv.appendChild(contentDiv);
                        sourcesList.appendChild(sourceDiv);
                    });
                    sourcesSection.style.display = 'block';
                }

                answerSection.style.display = 'block';
                
                // Scroll to answer
                answerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // Show error
                errorContent.textContent = data.error || 'An error occurred';
                errorSection.style.display = 'block';
                errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } catch (error) {
            // Remove progress message
            const progressMsg = document.getElementById('progressMsg');
            if (progressMsg) progressMsg.remove();
            
            // Reset button and cancel button
            submitBtn.disabled = false;
            if (cancelBtn) cancelBtn.style.display = 'none';
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            abortController = null;

            // Show error with helpful message
            let errorMsg = 'Network error: ' + error.message;
            if (error.name === 'AbortError' || error.message.includes('aborted')) {
                errorMsg = 'Query cancelled or timed out. The query is taking longer than expected. This might be due to Modal cold start (first query takes 10-15 seconds). Please try again - subsequent queries should be faster (3-5 seconds).';
            } else if (error.message.includes('Failed to fetch')) {
                errorMsg = 'Could not connect to server. Make sure the web app is running (python3 web_app.py)';
            }
            
            errorContent.textContent = errorMsg;
            errorSection.style.display = 'block';
            errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    // Allow Enter+Shift for new line, Enter alone to submit
    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
});

function setQuestion(question) {
    document.getElementById('questionInput').value = question;
    document.getElementById('questionInput').focus();
}

