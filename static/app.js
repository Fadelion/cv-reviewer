/**
 * ResumeAI Critiquer - Frontend Client Controller
 * Manages states, UI components, file uploads, persistent database memory history,
 * RAG guideline displays, and LLM structured schemas.
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements - Navigation & Outer Views
    const inputSection = document.getElementById('input-section');
    const loadingOverlay = document.getElementById('loading-overlay');
    const resultsSection = document.getElementById('results-section');
    const apiStatusIndicator = document.getElementById('api-status-indicator');
    
    // UI Elements - Forms & Inputs
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const resumeTextarea = document.getElementById('resume-text');
    const jdTextarea = document.getElementById('jd-text');
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnClearResume = document.getElementById('btn-clear-resume');
    const btnClearJd = document.getElementById('btn-clear-jd');
    const btnBack = document.getElementById('btn-back');
    const btnDownloadPdf = document.getElementById('btn-download-pdf');
    
    // UI Elements - Dashboard General
    const lblOverallScore = document.getElementById('lbl-overall-score');
    const lblScoreCommentary = document.getElementById('lbl-score-commentary');
    const overallGaugeValue = document.getElementById('overall-gauge-value');
    const resultsTimestamp = document.getElementById('results-timestamp');
    const lblExecSummary = document.getElementById('lbl-exec-summary');
    
    // UI Elements - Category Scores
    const lblImpactScore = document.getElementById('lbl-impact-score');
    const lblPresentationScore = document.getElementById('lbl-presentation-score');
    const lblExperienceScore = document.getElementById('lbl-experience-score');
    const lblKeywordsScore = document.getElementById('lbl-keywords-score');
    
    const barImpact = document.getElementById('bar-impact');
    const barPresentation = document.getElementById('bar-presentation');
    const barExperience = document.getElementById('bar-experience');
    const barKeywords = document.getElementById('bar-keywords');
    
    // UI Elements - Keyword Analytics
    const lblKeywordPercent = document.getElementById('lbl-keyword-percent');
    const keywordRingValue = document.getElementById('keyword-ring-value');
    const matchedTagsContainer = document.getElementById('matched-tags-container');
    const missingTagsContainer = document.getElementById('missing-tags-container');
    
    // UI Elements - Section Critiques Accordions
    const lblCritiqueSummary = document.getElementById('lbl-critique-summary');
    const lblCritiqueExperience = document.getElementById('lbl-critique-experience');
    const lblCritiqueProjects = document.getElementById('lbl-critique-projects');
    
    // UI Elements - Bullet Point Rewriter
    const bulletRewritesContainer = document.getElementById('bullet-rewrites-container');
    const lblRewriteCount = document.getElementById('lbl-rewrite-count');

    // UI Elements - History Panel
    const historyListBody = document.getElementById('history-list-body');
    const lblHistoryCount = document.getElementById('lbl-history-count');

    // UI Elements - RAG Guidelines
    const ragGuidelinesContainer = document.getElementById('rag-guidelines-container');

    // State Variables
    let uploadedFilename = "Pasted Resume";
    let currentCritiqueId = null;
    
    // Initialize icons
    lucide.createIcons();

    // Check Backend Server & API Connection on Load
    checkBackendHealth();

    // Load Critique History from persistent DB
    loadHistoryList();

    // Setup Textarea Clear button visibilities
    setupTextareaAutoClears();

    // Setup Drag and Drop Zone
    setupDragAndDrop();

    // Setup Tab Controller
    setupTabs();

    // Setup Accordions
    setupAccordions();

    // Analyze Click Handler
    btnAnalyze.addEventListener('click', handleAnalyzeResume);

    // Back Click Handler
    btnBack.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Download PDF Report Click Handler
    btnDownloadPdf.addEventListener('click', () => {
        if (btnDownloadPdf.disabled) {
            alert('PDF export is unavailable for this session. The analysis was not saved to the database.');
            return;
        }
        if (currentCritiqueId) {
            window.open(`/api/history/${currentCritiqueId}/pdf`, '_blank');
        } else {
            alert('No critique session ID available for export.');
        }
    });

    /**
     * Check backend API status
     */
    async function checkBackendHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (response.ok && data.status === 'healthy') {
                const statusDot = apiStatusIndicator.querySelector('.status-dot');
                const statusText = apiStatusIndicator.querySelector('.status-text');
                
                statusDot.className = 'status-dot pulses';
                statusDot.style.backgroundColor = '';
                statusDot.style.boxShadow = '';
                statusText.innerText = 'System Active';
                
                if (!data.api_key_configured) {
                    statusDot.style.backgroundColor = 'var(--clr-amber)';
                    statusDot.style.boxShadow = '0 0 10px var(--clr-amber)';
                    statusText.innerText = 'Missing API Key';
                }
            }
        } catch (error) {
            console.error('Error connecting to backend:', error);
            const statusDot = apiStatusIndicator.querySelector('.status-dot');
            const statusText = apiStatusIndicator.querySelector('.status-text');
            
            statusDot.className = 'status-dot';
            statusDot.style.backgroundColor = 'var(--clr-rose)';
            statusDot.style.boxShadow = '0 0 10px var(--clr-rose)';
            statusText.innerText = 'Offline Mode';
        }
    }

    /**
     * Clear Button Triggers for text fields
     */
    function setupTextareaAutoClears() {
        const toggleClearBtn = (textarea, btn) => {
            if (textarea.value.length > 0) {
                btn.classList.remove('hidden');
            } else {
                btn.classList.add('hidden');
            }
        };

        resumeTextarea.addEventListener('input', () => toggleClearBtn(resumeTextarea, btnClearResume));
        jdTextarea.addEventListener('input', () => toggleClearBtn(jdTextarea, btnClearJd));

        btnClearResume.addEventListener('click', () => {
            resumeTextarea.value = '';
            uploadedFilename = 'Pasted Resume';
            btnClearResume.classList.add('hidden');
            // Restore upload zone text
            uploadZone.querySelector('.upload-primary-text').innerHTML = `Drag & drop your CV here, or <span class="upload-browse">browse files</span>`;
        });

        btnClearJd.addEventListener('click', () => {
            jdTextarea.value = '';
            btnClearJd.classList.add('hidden');
        });
    }

    /**
     * File Drag & Drop Operations
     */
    function setupDragAndDrop() {
        // Trigger Browse
        uploadZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleUploadedFile(e.target.files[0]);
            }
        });

        // Drag/Drop Listeners
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadZone.classList.remove('dragover');
            }, false);
        });

        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleUploadedFile(files[0]);
            }
        });
    }

    /**
     * Process Uploaded PDF File
     */
    async function handleUploadedFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Currently, only standard PDF files are supported for auto-parsing.');
            return;
        }

        // Visual feedback
        const primaryText = uploadZone.querySelector('.upload-primary-text');
        primaryText.innerHTML = `<span class="text-indigo">Uploading ${file.name}...</span>`;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/extract-pdf', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                primaryText.innerHTML = `Successfully loaded <span class="text-emerald">${file.name}</span>`;
                resumeTextarea.value = data.text;
                uploadedFilename = file.name;
                btnClearResume.classList.remove('hidden');
                
                // Sparkle animation or micro-reaction
                uploadZone.style.borderColor = 'var(--clr-emerald)';
                setTimeout(() => {
                    uploadZone.style.borderColor = 'var(--border-subtle)';
                }, 2000);
            } else {
                primaryText.innerHTML = `Failed to parse file, or <span class="upload-browse">retry browsing</span>`;
                alert(data.error || 'Failed to extract text from PDF. Please ensure the file is not a scanned image.');
            }
        } catch (error) {
            console.error('File parsing error:', error);
            primaryText.innerHTML = `Error uploading, or <span class="upload-browse">retry browsing</span>`;
            alert('Server error while parsing PDF. Please try pasting raw text instead.');
        }
    }

    /**
     * Handle Tab Clicks
     */
    function setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTabId = button.getAttribute('data-tab');

                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');
                document.getElementById(targetTabId).classList.add('active');
            });
        });
    }

    /**
     * Accordions
     */
    function setupAccordions() {
        const accordionHeaders = document.querySelectorAll('.accordion-header');

        accordionHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const item = header.parentElement;
                const isExpanded = item.classList.contains('expanded');

                // Collapse all
                document.querySelectorAll('.accordion-item').forEach(i => {
                    i.classList.remove('expanded');
                });

                // Toggle selected
                if (!isExpanded) {
                    item.classList.add('expanded');
                }
            });
        });
    }

    /**
     * Handle LLM Analysis Submission
     */
    async function handleAnalyzeResume() {
        const resumeText = resumeTextarea.value.trim();
        const jdText = jdTextarea.value.trim();

        if (!resumeText) {
            alert('Please paste your Resume details or upload a PDF first.');
            resumeTextarea.focus();
            return;
        }

        // 1. Trigger beautiful Loading Overlay & Steps
        inputSection.classList.add('hidden');
        loadingOverlay.classList.remove('hidden');
        
        // Reset and start loading progress loop
        const steps = [
            document.getElementById('step-1'),
            document.getElementById('step-2'),
            document.getElementById('step-3'),
            document.getElementById('step-4')
        ];
        
        steps.forEach(step => {
            step.className = 'step-item';
            step.querySelector('.step-status').innerHTML = '<i data-lucide="circle"></i>';
        });
        lucide.createIcons({ attrs: { class: 'icon-style' } });

        // Sequentially activate loading steps
        let currentStep = 0;
        steps[0].classList.add('active');
        steps[0].querySelector('.step-status').innerHTML = '<i data-lucide="loader-2" class="animate-spin text-indigo"></i>';
        lucide.createIcons();

        const stepInterval = setInterval(() => {
            if (currentStep < steps.length - 1) {
                // Complete previous step
                steps[currentStep].className = 'step-item completed';
                steps[currentStep].querySelector('.step-status').innerHTML = '<i data-lucide="check-circle-2" class="text-emerald"></i>';
                
                // Activate next step
                currentStep++;
                steps[currentStep].classList.add('active');
                steps[currentStep].querySelector('.step-status').innerHTML = '<i data-lucide="loader-2" class="animate-spin text-indigo"></i>';
                lucide.createIcons();
            }
        }, 1800);

        try {
            // Send API call to FastAPI backend
            const response = await fetch('/api/review', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    resume_text: resumeText,
                    job_description: jdText,
                    filename: uploadedFilename
                })
            });

            const data = await response.json();

            // Clear loading timers
            clearInterval(stepInterval);

            if (response.ok) {
                // Ensure all steps look complete
                steps.forEach(step => {
                    step.className = 'step-item completed';
                    step.querySelector('.step-status').innerHTML = '<i data-lucide="check-circle-2" class="text-emerald"></i>';
                });
                lucide.createIcons();

                // Wait briefly for user to feel completion, then reveal Dashboard
                setTimeout(() => {
                    loadingOverlay.classList.add('hidden');
                    resultsSection.classList.remove('hidden');
                    
                    // Capture the critique ID
                    currentCritiqueId = data.id || null;
                    
                    // Render the structured results dashboard
                    renderAnalysisDashboard(data, currentCritiqueId);
                    
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }, 800);

            } else {
                loadingOverlay.classList.add('hidden');
                inputSection.classList.remove('hidden');
                alert(data.error || 'Server error occurred during CV analysis.');
            }

        } catch (error) {
            console.error('Submission error:', error);
            clearInterval(stepInterval);
            loadingOverlay.classList.add('hidden');
            inputSection.classList.remove('hidden');
            alert('Failed to connect to AI reviewer server. Please ensure application backend is running.');
        }
    }

    /**
     * Render the structured analysis feedback onto the dashboard
     */
    function renderAnalysisDashboard(data, critiqueId) {
        // Resolve critique ID: prefer explicitly passed value, fall back to data.id
        const resolvedId = critiqueId || (data && data.id) || null;
        if (resolvedId !== null && resolvedId !== undefined) {
            currentCritiqueId = resolvedId;
        }

        // Always show PDF export button — it's only functional when we have an ID
        if (currentCritiqueId) {
            btnDownloadPdf.style.display = 'flex';
            btnDownloadPdf.disabled = false;
            btnDownloadPdf.style.opacity = '1';
            btnDownloadPdf.title = 'Download PDF report';
        } else {
            // Still show the button but disable it so user knows it exists
            btnDownloadPdf.style.display = 'flex';
            btnDownloadPdf.disabled = true;
            btnDownloadPdf.title = 'PDF export unavailable (session not saved)';
            btnDownloadPdf.style.opacity = '0.4';
        }

        // 1. Date / Timestamp
        const now = new Date();
        resultsTimestamp.innerText = `ANALYSIS REF: ${now.toISOString().substring(0, 10).replace(/-/g, '')}-${Math.floor(1000 + Math.random() * 9000)}`;

        // 2. Score comment commentary
        let commentary = "Excellent CV. Highly competitive.";
        if (data.overall_score < 50) commentary = "Critical updates required to pass screening.";
        else if (data.overall_score < 70) commentary = "Good base. Needs impact formatting.";
        else if (data.overall_score < 85) commentary = "Strong matching profile. Optimizations recommended.";
        lblScoreCommentary.innerText = commentary;

        // 3. Overall SVG Circle progress
        // Calculate circumference: 2 * Math.PI * radius = 2 * 3.14159 * 50 = 314.15
        const overallCircumference = 314;
        const overallOffset = overallCircumference - (data.overall_score / 100) * overallCircumference;
        
        // Trigger counter incremental animation
        animateCounter(lblOverallScore, 0, data.overall_score, 1200);
        
        // Trigger dashoffset animation
        overallGaugeValue.style.strokeDashoffset = overallCircumference; // Reset first
        setTimeout(() => {
            overallGaugeValue.style.strokeDashoffset = overallOffset;
        }, 100);

        // 4. Exec summary
        lblExecSummary.innerText = data.summary;

        // 5. Grid category scores
        animateProgressBars(data.scores);

        // 6. Strengths & Improvements
        populateSplitFeedback(data.strengths, data.improvements);

        // 7. Keyword gap ring & list
        populateKeywordAnalysis(data.keyword_analysis);

        // 8. Section Critique accordions
        lblCritiqueSummary.innerText = data.section_critique.summary || "No specific summary feedback.";
        lblCritiqueExperience.innerText = data.section_critique.experience || "No specific experience critique.";
        lblCritiqueProjects.innerText = data.section_critique.projects_skills || "No specific skills or projects critique.";

        // 9. Bullet Rewriter List
        populateBulletRewriter(data.bullet_rewrites);

        // 10. RAG retrieved guidelines
        populateRagGuidelines(data.retrieved_context);

        // 11. Refresh Persistent SQLite memory history
        loadHistoryList();

        // 12. Re-trigger lucide icons
        lucide.createIcons();
    }

    /**
     * Counter score animator
     */
    function animateCounter(element, start, end, duration) {
        let startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            element.innerText = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        }
        window.requestAnimationFrame(step);
    }

    /**
     * Animate dashboard bars and numeric texts
     */
    function animateProgressBars(scores) {
        // Values text
        lblImpactScore.innerText = `${scores.impact}%`;
        lblPresentationScore.innerText = `${scores.presentation}%`;
        lblExperienceScore.innerText = `${scores.experience}%`;
        lblKeywordsScore.innerText = `${scores.keywords}%`;

        // Progress bar fills
        setTimeout(() => {
            barImpact.style.width = `${scores.impact}%`;
            barPresentation.style.width = `${scores.presentation}%`;
            barExperience.style.width = `${scores.experience}%`;
            barKeywords.style.width = `${scores.keywords}%`;
        }, 150);
    }

    /**
     * Create strength and improvement nodes
     */
    function populateSplitFeedback(strengths, improvements) {
        const strengthsList = document.getElementById('strengths-list');
        const improvementsList = document.getElementById('improvements-list');
        
        strengthsList.innerHTML = '';
        improvementsList.innerHTML = '';

        // Strengths
        if (strengths && strengths.length > 0) {
            strengths.forEach(item => {
                const card = document.createElement('div');
                card.className = 'feedback-item-card border-success';
                card.innerHTML = `
                    <div class="feedback-item-header">
                        <span class="feedback-item-category cat-success">${escapeHtml(item.category)}</span>
                    </div>
                    <div class="feedback-item-point">${escapeHtml(item.point)}</div>
                    <div class="feedback-item-detail">${escapeHtml(item.detail)}</div>
                `;
                strengthsList.appendChild(card);
            });
        } else {
            strengthsList.innerHTML = `<div class="feedback-item-card"><p class="text-muted">No specific strengths isolated.</p></div>`;
        }

        // Improvements
        if (improvements && improvements.length > 0) {
            improvements.forEach(item => {
                const card = document.createElement('div');
                card.className = 'feedback-item-card border-danger';
                card.innerHTML = `
                    <div class="feedback-item-header">
                        <span class="feedback-item-category cat-danger">${escapeHtml(item.category)}</span>
                    </div>
                    <div class="feedback-item-point">${escapeHtml(item.point)}</div>
                    <div class="feedback-item-detail">${escapeHtml(item.detail)}</div>
                `;
                improvementsList.appendChild(card);
            });
        } else {
            improvementsList.innerHTML = `<div class="feedback-item-card"><p class="text-muted">Perfect score! No immediate areas of improvement required.</p></div>`;
        }
    }

    /**
     * Populate ATS Tag and Match percentage
     */
    function populateKeywordAnalysis(keywordData) {
        matchedTagsContainer.innerHTML = '';
        missingTagsContainer.innerHTML = '';

        // Ring Circumference: 2 * Math.PI * 40 = 251.3
        const ringCircumference = 251;
        const ringOffset = ringCircumference - (keywordData.critical_percentage / 100) * ringCircumference;
        
        lblKeywordPercent.innerText = `${keywordData.critical_percentage}%`;
        
        // Reset and trigger ring stroke offset
        keywordRingValue.style.strokeDashoffset = ringCircumference;
        setTimeout(() => {
            keywordRingValue.style.strokeDashoffset = ringOffset;
        }, 200);

        // Matched Tags
        if (keywordData.matched && keywordData.matched.length > 0) {
            keywordData.matched.forEach(tag => {
                const span = document.createElement('span');
                span.className = 'badge-tag tag-matched';
                span.innerText = tag;
                matchedTagsContainer.appendChild(span);
            });
        } else {
            matchedTagsContainer.innerHTML = '<span class="text-muted fs-085">No major competencies detected.</span>';
        }

        // Missing Tags
        if (keywordData.missing && keywordData.missing.length > 0) {
            keywordData.missing.forEach(tag => {
                const span = document.createElement('span');
                span.className = 'badge-tag tag-missing';
                span.innerText = tag;
                missingTagsContainer.appendChild(span);
            });
        } else {
            missingTagsContainer.innerHTML = '<span class="text-muted fs-085">None missing! Perfectly tailored keyword layout.</span>';
        }
    }

    /**
     * Render Comparative STAR Bullet Rewrites
     */
    function populateBulletRewriter(bulletRewrites) {
        bulletRewritesContainer.innerHTML = '';
        
        if (!bulletRewrites || bulletRewrites.length === 0) {
            lblRewriteCount.innerText = '0';
            bulletRewritesContainer.innerHTML = `
                <div class="bullet-rewrite-card" style="text-align:center;">
                    <p class="text-muted">No passive bullets identified for rewriting. Great usage of the STAR format!</p>
                </div>
            `;
            return;
        }

        lblRewriteCount.innerText = bulletRewrites.length;

        bulletRewrites.forEach((bullet, index) => {
            const card = document.createElement('div');
            card.className = 'bullet-rewrite-card';
            
            card.innerHTML = `
                <div class="bullet-comparison-flow">
                    <!-- Left: Original -->
                    <div class="bullet-pane pane-original">
                        <div class="pane-label">
                            <i data-lucide="x-circle"></i>
                            <span>Original</span>
                        </div>
                        <div class="pane-content">"${escapeHtml(bullet.original)}"</div>
                    </div>
                    
                    <!-- Right: Improved -->
                    <div class="bullet-pane pane-improved" title="Click to Copy optimized text">
                        <div class="pane-label">
                            <i data-lucide="check-circle-2"></i>
                            <span>Optimised (STAR)</span>
                        </div>
                        <div class="pane-content" id="bullet-improved-text-${index}">"${escapeHtml(bullet.improved)}"</div>
                    </div>
                </div>
 
                <!-- Card Footer Actions -->
                <div class="bullet-card-footer">
                    <div class="bullet-rationale">
                        <i data-lucide="lightbulb"></i>
                        <span><strong>Rationale:</strong> ${escapeHtml(bullet.rationale)}</span>
                    </div>
                    <button class="btn-action-copy" data-copy-index="${index}">
                        <i data-lucide="copy"></i>
                        <span>Copy</span>
                    </button>
                </div>
            `;

            bulletRewritesContainer.appendChild(card);
        });

        // Attach Copy Handlers to newly created elements
        attachCopyHandlers();
    }

    /**
     * Render retrieved RAG guidelines
     */
    function populateRagGuidelines(guidelines) {
        ragGuidelinesContainer.innerHTML = '';
        
        if (!guidelines || guidelines.length === 0) {
            ragGuidelinesContainer.innerHTML = `
                <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
                    <p>No guidelines were retrieved from the context database for this session.</p>
                </div>
            `;
            return;
        }

        guidelines.forEach(g => {
            const card = document.createElement('div');
            card.style.background = 'var(--bg-card)';
            card.style.border = '1px solid var(--border-subtle)';
            card.style.borderLeft = '4px solid var(--clr-cyan)';
            card.style.borderRadius = 'var(--radius-card)';
            card.style.padding = '1.5rem';
            card.style.display = 'flex';
            card.style.flexDirection = 'column';
            card.style.gap = '0.75rem';

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="background: hsla(185, 90%, 50%, 0.12); color: var(--clr-cyan); padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                        ${escapeHtml(g.category)}
                    </span>
                    <span style="color: var(--text-muted); font-size: 0.75rem; font-family: monospace;">RULE_ID: ${escapeHtml(g.id)}</span>
                </div>
                <h4 style="font-family: var(--font-heading); font-size: 1.15rem; font-weight: 600; color: var(--text-primary);">
                    ${escapeHtml(g.title)}
                </h4>
                <p style="color: var(--text-secondary); font-size: 0.92rem; line-height: 1.5;">
                    ${escapeHtml(g.content)}
                </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; background: hsla(220, 20%, 6%, 0.4); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-subtle); margin-top: 0.5rem;">
                    <div>
                        <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--clr-rose); font-weight: 800; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 4px;">
                            <i data-lucide="x-circle" style="width:12px; height:12px;"></i> Common Weak Pattern
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">"${escapeHtml(g.examples.before)}"</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--clr-emerald); font-weight: 800; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 4px;">
                            <i data-lucide="check-circle-2" style="width:12px; height:12px;"></i> Optimized (STAR Impact)
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-primary); font-weight: 500;">"${escapeHtml(g.examples.after)}"</div>
                    </div>
                </div>
            `;
            ragGuidelinesContainer.appendChild(card);
        });
    }

    /**
     * Load Persistent SQLite Memory Critique History
     */
    async function loadHistoryList() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();

            if (response.ok) {
                lblHistoryCount.innerText = `${data.length} Session${data.length !== 1 ? 's' : ''}`;
                
                if (data.length === 0) {
                    historyListBody.innerHTML = `
                        <tr>
                            <td colspan="6" style="padding: 24px; text-align: center; color: var(--text-muted);">
                                <i data-lucide="database-backup" style="width: 24px; height: 24px; margin-bottom: 8px; opacity: 0.5; display: inline-block;"></i>
                                <p>No past analysis sessions saved in memory. Critique a CV to populate this log.</p>
                            </td>
                        </tr>
                    `;
                    lucide.createIcons();
                    return;
                }

                historyListBody.innerHTML = '';
                data.forEach(item => {
                    // Format Date
                    const d = new Date(item.timestamp);
                    const formattedDate = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
                    
                    // Score Color Badge
                    let scoreBadgeColor = 'hsla(352, 85%, 60%, 0.15)';
                    let scoreTextColor = 'var(--clr-rose)';
                    let scoreBorderColor = 'hsla(352, 85%, 60%, 0.3)';
                    
                    if (item.overall_score >= 80) {
                        scoreBadgeColor = 'hsla(145, 75%, 48%, 0.15)';
                        scoreTextColor = 'var(--clr-emerald)';
                        scoreBorderColor = 'hsla(145, 75%, 48%, 0.3)';
                    } else if (item.overall_score >= 50) {
                        scoreBadgeColor = 'hsla(40, 95%, 58%, 0.15)';
                        scoreTextColor = 'var(--clr-amber)';
                        scoreBorderColor = 'hsla(40, 95%, 58%, 0.3)';
                    }

                    const tr = document.createElement('tr');
                    tr.style.borderBottom = '1px solid var(--border-subtle)';
                    tr.style.transition = 'background 0.2s';
                    tr.addEventListener('mouseenter', () => tr.style.background = 'hsla(220, 20%, 12%, 0.3)');
                    tr.addEventListener('mouseleave', () => tr.style.background = '');

                    tr.innerHTML = `
                        <td style="padding: 12px 16px; color: var(--text-muted); font-size: 0.88rem;">${escapeHtml(formattedDate)}</td>
                        <td style="padding: 12px 16px; font-weight: 500; color: var(--text-primary); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <i data-lucide="file-text" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 6px; color: var(--clr-indigo);"></i>
                            <span style="vertical-align: middle;">${escapeHtml(item.filename)}</span>
                        </td>
                        <td style="padding: 12px 16px; color: var(--text-secondary); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${escapeHtml(item.job_title || 'General Critique')}
                        </td>
                        <td style="padding: 12px 16px; text-align: center;">
                            <span style="background: ${scoreBadgeColor}; color: ${scoreTextColor}; border: 1px solid ${scoreBorderColor}; padding: 3px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 700;">
                                ${item.overall_score}/100
                            </span>
                        </td>
                        <td style="padding: 12px 16px; text-align: center; color: var(--clr-cyan); font-weight: 600;">
                            ${item.keyword_match}%
                        </td>
                        <td style="padding: 12px 16px; text-align: right;">
                            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                                <button class="btn-action-load" data-id="${item.id}" style="background: hsla(250, 90%, 65%, 0.15); border: 1px solid hsla(250, 90%, 65%, 0.3); color: var(--clr-indigo); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 4px;">
                                    <i data-lucide="arrow-right-circle" style="width:12px; height:12px;"></i> View
                                </button>
                                <button class="btn-action-pdf" data-id="${item.id}" style="background: hsla(185, 90%, 50%, 0.15); border: 1px solid hsla(185, 90%, 50%, 0.3); color: var(--clr-cyan); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 4px;">
                                    <i data-lucide="file-down" style="width:12px; height:12px;"></i> PDF
                                </button>
                                <button class="btn-action-delete" data-id="${item.id}" style="background: hsla(352, 85%, 60%, 0.1); border: 1px solid hsla(352, 85%, 60%, 0.2); color: var(--clr-rose); padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; cursor: pointer; transition: all 0.2s;">
                                    <i data-lucide="trash-2" style="width:12px; height:12px;"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    historyListBody.appendChild(tr);
                });
                
                // Add event listeners to history action buttons
                attachHistoryHandlers();
                lucide.createIcons();
            }
        } catch (error) {
            console.error('Error fetching critique history database:', error);
        }
    }

    /**
     * Attach Load and Delete Click Handlers on History list items
     */
    function attachHistoryHandlers() {
        // Load critique
        document.querySelectorAll('.btn-action-load').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const critiqueId = btn.getAttribute('data-id');
                btn.innerHTML = '<i data-lucide="loader-2" class="animate-spin" style="width:12px; height:12px;"></i> Loading';
                lucide.createIcons();
                
                try {
                    const response = await fetch(`/api/history/${critiqueId}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        // Switch panel views instantly (no loading animation)
                        inputSection.classList.add('hidden');
                        resultsSection.classList.remove('hidden');
                        
                        // Parse resume texts back to inputs for convenience
                        resumeTextarea.value = data.cv_text || '';
                        jdTextarea.value = data.job_description || '';
                        uploadedFilename = data.filename || 'Pasted Resume';
                        
                        // Trigger buttons updates
                        if (resumeTextarea.value) btnClearResume.classList.remove('hidden');
                        if (jdTextarea.value) btnClearJd.classList.remove('hidden');
                        
                        // Store the current loaded critique ID
                        currentCritiqueId = critiqueId;
                        
                        // Render dashboard!
                        renderAnalysisDashboard(data.result_json, critiqueId);
                        
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    } else {
                        alert('Could not fetch saved session details.');
                        loadHistoryList();
                    }
                } catch (err) {
                    console.error('Error fetching history detail:', err);
                    alert('Error communicating with history API.');
                }
            });
        });

        // Delete critique
        document.querySelectorAll('.btn-action-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const critiqueId = btn.getAttribute('data-id');
                if (!confirm('Are you sure you want to permanently delete this critique record?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/history/${critiqueId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        loadHistoryList();
                    } else {
                        alert('Error deleting history record.');
                    }
                } catch (err) {
                    console.error('Error deleting record:', err);
                }
            });
        });

        // Download critique PDF from history table list
        document.querySelectorAll('.btn-action-pdf').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const critiqueId = btn.getAttribute('data-id');
                window.open(`/api/history/${critiqueId}/pdf`, '_blank');
            });
        });
    }

    /**
     * Copy functionality for rewrites
     */
    function attachCopyHandlers() {
        // Individual buttons copy
        const copyButtons = document.querySelectorAll('.btn-action-copy');
        copyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = btn.getAttribute('data-copy-index');
                const targetText = document.getElementById(`bullet-improved-text-${idx}`).innerText.replace(/^"|"$/g, '');
                
                navigator.clipboard.writeText(targetText).then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.style.backgroundColor = 'var(--clr-emerald)';
                    btn.style.borderColor = 'var(--clr-emerald)';
                    btn.style.color = '#white';
                    btn.innerHTML = '<i data-lucide="check"></i><span>Copied!</span>';
                    lucide.createIcons();

                    setTimeout(() => {
                        btn.style.backgroundColor = '';
                        btn.style.borderColor = '';
                        btn.style.color = '';
                        btn.innerHTML = originalHTML;
                        lucide.createIcons();
                    }, 2000);
                });
            });
        });

        // Direct clicking on improved pane copies as well
        const improvedPanes = document.querySelectorAll('.pane-improved');
        improvedPanes.forEach((pane, idx) => {
            pane.style.cursor = 'pointer';
            pane.addEventListener('click', () => {
                const btn = document.querySelector(`.btn-action-copy[data-copy-index="${idx}"]`);
                if (btn) btn.click();
            });
        });
    }

    /**
     * Escape HTML helper
     */
    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
