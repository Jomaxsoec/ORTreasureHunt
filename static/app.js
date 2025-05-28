// Main JavaScript for Treasure Hunt Game

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    showAlert('An unexpected error occurred. Please try again.', 'danger');
});

// Utility function to show alerts
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    alertContainer.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Main form submission for treasure hunt
async function submitTeamCredentials() {
    const form = document.getElementById('teamForm');
    if (!form) return;

    const submitBtn = document.getElementById('submitBtn');
    const teamName = document.getElementById('teamName').value.trim();
    const teamCode = document.getElementById('teamCode').value.trim();
    const qrId = document.getElementById('qrId').value.trim();

    // Validate input
    if (!teamName || !teamCode || !qrId) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    // Disable submit button
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';
    }

    try {
        const response = await fetch('/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                team_name: teamName,
                team_code: teamCode,
                qr_id: qrId
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(`Success! Your code is: <strong>${data.assigned_code}</strong>`, 'success');
            form.reset();
        } else {
            showAlert(data.error || 'Verification failed', 'danger');
        }

    } catch (error) {
        console.error('Error:', error);
        showAlert('Network error. Please check your connection and try again.', 'danger');
    } finally {
        // Re-enable submit button
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Verify & Get Code';
        }
    }
}

// Admin functions
async function loadAssignedCodes() {
    try {
        const response = await fetch('/codes');
        const data = await response.json();

        const tableBody = document.getElementById('codesTableBody');
        if (!tableBody) return;

        if (data.success) {
            if (data.assigned_codes.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            <i class="fas fa-inbox me-2"></i>
                            No codes assigned yet
                        </td>
                    </tr>
                `;
            } else {
                tableBody.innerHTML = data.assigned_codes.map(code => `
                    <tr>
                        <td>${code.team_name}</td>
                        <td>Q${code.question_number}</td>
                        <td><code>${code.assigned_code}</code></td>
                        <td>${new Date(code.assigned_at).toLocaleString()}</td>
                        <td><small class="text-muted">${code.device_fingerprint}</small></td>
                        <td>
                            <span class="badge bg-success">Assigned</span>
                        </td>
                    </tr>
                `).join('');
            }
        } else {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">
                        Error loading data: ${data.error}
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading codes:', error);
        const tableBody = document.getElementById('codesTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">
                        Network error loading data
                    </td>
                </tr>
            `;
        }
    }
}

async function loadStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();

        if (data.success) {
            // Update stats cards
            const uniqueTeamsElement = document.getElementById('uniqueTeams');
            if (uniqueTeamsElement) {
                uniqueTeamsElement.textContent = data.unique_teams;
            }

            // Update question stats
            for (let i = 1; i <= 9; i++) {
                const questionStats = data.stats[`question_${i}`];
                if (questionStats) {
                    const assignedElement = document.getElementById(`q${i}Assigned`);
                    const availableElement = document.getElementById(`q${i}Available`);

                    if (assignedElement) assignedElement.textContent = questionStats.assigned;
                    if (availableElement) availableElement.textContent = questionStats.available;
                }
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function syncExternalData() {
    const syncBtn = document.getElementById('syncBtn');
    if (!syncBtn) return;

    syncBtn.disabled = true;
    syncBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Syncing...';

    try {
        const response = await fetch('/sync', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showAlert(data.message, 'success');
            // Reload the page data
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showAlert(data.error, 'danger');
        }
    } catch (error) {
        console.error('Error syncing:', error);
        showAlert('Network error during sync', 'danger');
    } finally {
        syncBtn.disabled = false;
        syncBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Sync External Data';
    }
}

async function resetGameData() {
    if (!confirm('Are you sure you want to reset all game data? This will clear all team access and assigned codes. This action cannot be undone.')) {
        return;
    }

    const resetBtn = document.getElementById('resetBtn');
    if (!resetBtn) return;

    resetBtn.disabled = true;
    resetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Resetting...';

    try {
        const response = await fetch('/reset', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showAlert(data.message, 'success');
            // Reload the page
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showAlert(data.error, 'danger');
        }
    } catch (error) {
        console.error('Error resetting:', error);
        showAlert('Network error during reset', 'danger');
    } finally {
        resetBtn.disabled = false;
        resetBtn.innerHTML = '<i class="fas fa-trash-alt me-2"></i>Reset Game Data';
    }
}

// Treasure Hunt Game JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('verifyForm');
    const alertContainer = document.getElementById('alertContainer');
    const submitBtn = document.getElementById('submitBtn');

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Get form data
            const teamName = document.getElementById('teamName').value.trim();
            const teamCode = document.getElementById('teamCode').value.trim();
            const qrId = document.getElementById('qrId').value.trim();

            // Validate input
            if (!teamName || !teamCode || !qrId) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }

            if (qrId < 1 || qrId > 9) {
                showAlert('QR ID must be between 1 and 9', 'danger');
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Verifying...';

            try {
                const response = await fetch('/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        team_name: teamName,
                        team_code: teamCode,
                        qr_id: qrId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showSuccessResult(data);
                } else {
                    showAlert(data.error || 'Verification failed', 'danger');
                }

            } catch (error) {
                console.error('Error:', error);
                showAlert('Network error. Please try again.', 'danger');
            } finally {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check me-2"></i>Verify & Get Code';
            }
        });
    }
});

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    alertContainer.innerHTML = alertHtml;

    // Auto-dismiss after 5 seconds for non-success alerts
    if (type !== 'success') {
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                try {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                } catch (e) {
                    alert.remove();
                }
            }
        }, 5000);
    }
}

function showSuccessResult(data) {
    const alertContainer = document.getElementById('alertContainer');
    const successHtml = `
        <div class="alert alert-success" role="alert">
            <div class="text-center">
                <h4 class="alert-heading">
                    <i class="fas fa-check-circle me-2"></i>
                    Success!
                </h4>
                <hr>
                <div class="mb-3">
                    <strong>Team:</strong> ${data.team_name}<br>
                    <strong>Question:</strong> ${data.question_number}
                </div>
                <div class="bg-light p-3 rounded">
                    <h3 class="display-4 text-primary mb-0" style="font-family: 'Courier New', monospace;">
                        ${data.assigned_code}
                    </h3>
                    <small class="text-muted">Your unique code</small>
                </div>
                <div class="mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Save this code - you'll need it to proceed!
                    </small>
                </div>
            </div>
        </div>
    `;
    alertContainer.innerHTML = successHtml;

    // Scroll to result
    alertContainer.scrollIntoView({ behavior: 'smooth' });
}