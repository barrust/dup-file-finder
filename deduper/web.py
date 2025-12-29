"""
Web interface for deduper.
"""

from flask import Flask, render_template_string, jsonify, request
from .core import FileDuplicateFinder


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deduper - Duplicate File Finder</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card h3 {
            font-size: 0.9em;
            margin-bottom: 10px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
        }
        
        .btn-danger {
            background: #f56565;
            color: white;
        }
        
        .btn-danger:hover {
            background: #e53e3e;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(245, 101, 101, 0.4);
        }
        
        .btn-secondary {
            background: #e2e8f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #cbd5e0;
        }
        
        .duplicates-section {
            margin-top: 30px;
        }
        
        .duplicate-group {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .duplicate-group h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .file-list {
            list-style: none;
        }
        
        .file-item {
            padding: 10px;
            background: white;
            border-radius: 4px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .file-path {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #4a5568;
            word-break: break-all;
        }
        
        .message {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        
        .message-info {
            background: #bee3f8;
            color: #2c5282;
        }
        
        .message-success {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .message-warning {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Deduper</h1>
        <p class="subtitle">Find and manage duplicate files</p>
        
        <div class="stats-grid" id="stats">
            <div class="stat-card">
                <h3>Total Files</h3>
                <div class="value" id="total-files">0</div>
            </div>
            <div class="stat-card">
                <h3>Unique Files</h3>
                <div class="value" id="unique-files">0</div>
            </div>
            <div class="stat-card">
                <h3>Duplicate Files</h3>
                <div class="value" id="duplicate-files">0</div>
            </div>
            <div class="stat-card">
                <h3>Duplicate Groups</h3>
                <div class="value" id="duplicate-groups">0</div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
            <button class="btn btn-primary" onclick="findDuplicates()">🔎 Find Duplicates</button>
            <button class="btn btn-danger" onclick="deleteDuplicates()">🗑️ Delete Duplicates (Dry Run)</button>
        </div>
        
        <div id="message-area"></div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Loading...</p>
        </div>
        
        <div class="duplicates-section" id="duplicates-section"></div>
    </div>
    
    <script>
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showMessage(message, type = 'info') {
            const messageArea = document.getElementById('message-area');
            messageArea.innerHTML = `<div class="message message-${type}">${message}</div>`;
            setTimeout(() => {
                messageArea.innerHTML = '';
            }, 5000);
        }
        
        function formatSize(bytes) {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = bytes;
            let unitIndex = 0;
            
            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }
            
            return `${size.toFixed(2)} ${units[unitIndex]}`;
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('total-files').textContent = stats.total_files;
                document.getElementById('unique-files').textContent = stats.unique_files;
                document.getElementById('duplicate-files').textContent = stats.duplicate_files;
                document.getElementById('duplicate-groups').textContent = stats.duplicate_groups;
            } catch (error) {
                showMessage('Error loading statistics', 'warning');
            }
        }
        
        async function findDuplicates() {
            showLoading();
            try {
                const response = await fetch('/api/duplicates');
                const data = await response.json();
                
                const section = document.getElementById('duplicates-section');
                
                if (data.duplicates.length === 0) {
                    section.innerHTML = '<div class="message message-info">No duplicate files found!</div>';
                } else {
                    let html = '<h2>Duplicate File Groups</h2>';
                    
                    data.duplicates.forEach((group, index) => {
                        html += `
                            <div class="duplicate-group">
                                <h3>Group ${index + 1} (${group.length} files)</h3>
                                <ul class="file-list">
                                    ${group.map(file => `
                                        <li class="file-item">
                                            <span class="file-path">${file}</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        `;
                    });
                    
                    section.innerHTML = html;
                    showMessage(`Found ${data.duplicates.length} groups of duplicate files`, 'success');
                }
            } catch (error) {
                showMessage('Error finding duplicates', 'warning');
            } finally {
                hideLoading();
            }
        }
        
        async function deleteDuplicates() {
            if (!confirm('This will show what files would be deleted (dry run). Continue?')) {
                return;
            }
            
            showLoading();
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ dry_run: true })
                });
                
                const data = await response.json();
                
                if (data.deleted.length === 0) {
                    showMessage('No duplicate files to delete', 'info');
                } else {
                    const section = document.getElementById('duplicates-section');
                    let html = '<h2>Files that would be deleted (Dry Run)</h2>';
                    html += '<div class="duplicate-group">';
                    html += '<ul class="file-list">';
                    
                    data.deleted.forEach(file => {
                        html += `
                            <li class="file-item">
                                <span class="file-path">${file}</span>
                            </li>
                        `;
                    });
                    
                    html += '</ul></div>';
                    section.innerHTML = html;
                    
                    showMessage(`Would delete ${data.deleted.length} files (dry run mode)`, 'warning');
                }
                
                await loadStats();
            } catch (error) {
                showMessage('Error deleting duplicates', 'warning');
            } finally {
                hideLoading();
            }
        }
        
        async function refreshData() {
            showLoading();
            await loadStats();
            showMessage('Statistics refreshed', 'success');
            hideLoading();
        }
        
        // Load stats on page load
        document.addEventListener('DOMContentLoaded', loadStats);
    </script>
</body>
</html>
"""


def create_app(finder: FileDuplicateFinder):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['finder'] = finder

    @app.route('/')
    def index():
        """Render the main page."""
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/stats')
    def get_stats():
        """Get statistics about files and duplicates."""
        finder = app.config['finder']
        stats = finder.get_statistics()
        return jsonify(stats)

    @app.route('/api/duplicates')
    def get_duplicates():
        """Get all duplicate file groups."""
        finder = app.config['finder']
        groups = finder.get_duplicate_groups()
        return jsonify({'duplicates': groups})

    @app.route('/api/delete', methods=['POST'])
    def delete_duplicates():
        """Delete duplicate files."""
        finder = app.config['finder']
        data = request.get_json() or {}
        dry_run = data.get('dry_run', True)
        keep_first = data.get('keep_first', True)
        
        deleted = finder.delete_duplicates(keep_first=keep_first, dry_run=dry_run)
        return jsonify({'deleted': deleted})

    return app
