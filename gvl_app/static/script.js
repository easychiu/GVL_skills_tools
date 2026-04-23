// GVL 裝備表前端 JavaScript

// 全局狀態
let state = {
    currentPage: 1,
    perPage: 20,
    totalPages: 1
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化頁面
function initializePage() {
    loadPositions();
    loadSkills();
    loadEquipmentPage();
    loadStats();
    setupTabHandlers();
}

// 設置標籤處理器
function setupTabHandlers() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

// 切換標籤
function switchTab(tabName) {
    // 隱藏所有標籤內容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 移除所有按鈕的活躍狀態
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 顯示選中的標籤
    document.getElementById(tabName).classList.add('active');
    
    // 標記按鈕為活躍
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// 加載位置列表
function loadPositions() {
    fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('positionSelect');
            data.positions.forEach(position => {
                const option = document.createElement('option');
                option.value = position;
                option.textContent = position;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading positions:', error));
}

// 加載技能列表
function loadSkills() {
    fetch('/api/skills')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('skillSelect');
            data.skills.forEach(skill => {
                const option = document.createElement('option');
                option.value = skill;
                option.textContent = skill;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading skills:', error));
}

// 按名稱搜索
function searchByName() {
    const keyword = document.getElementById('searchName').value.trim();
    if (!keyword) {
        alert('請輸入搜索關鍵字');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(keyword)}&type=name`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 按技能搜索
function searchBySkill() {
    const skill = document.getElementById('skillSelect').value;
    const minLevel = parseInt(document.getElementById('minLevel').value) || 1;
    
    if (!skill) {
        alert('請選擇技能');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(skill)}&type=skill&min_level=${minLevel}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 按位置搜索
function searchByPosition() {
    const position = document.getElementById('positionSelect').value;
    
    if (!position) {
        alert('請選擇位置');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(position)}&type=position`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 顯示搜索結果
function displaySearchResults(data) {
    const resultsDiv = document.getElementById('searchResults');
    const resultsList = document.getElementById('resultsList');
    
    if (data.results.length === 0) {
        resultsList.innerHTML = '<div class="error">未找到匹配的結果</div>';
    } else {
        resultsList.innerHTML = '';
        
        // 創建表格
        const table = document.createElement('table');
        table.className = 'equipment-table';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>位置</th>
                <th>裝備名稱</th>
                <th>技能加成</th>
            </tr>
        `;
        table.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        data.results.forEach(eq => {
            const skillsStr = Object.entries(eq.skills)
                .map(([skill, level]) => `${skill}(+${level})`)
                .join(', ') || '無';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${eq.position}</td>
                <td>${eq.name}</td>
                <td>${skillsStr}</td>
            `;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        resultsList.appendChild(table);
    }
    
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// 加載裝備頁面
function loadEquipmentPage() {
    fetch(`/api/equipment?page=${state.currentPage}&per_page=${state.perPage}`)
        .then(response => response.json())
        .then(data => {
            state.totalPages = data.pages;
            displayEquipmentGrid(data.equipment);
            updatePageInfo(data);
        })
        .catch(error => console.error('Error loading equipment:', error));
}

// 顯示裝備網格
function displayEquipmentGrid(equipment) {
    const grid = document.getElementById('equipmentList');
    grid.innerHTML = '';
    
    equipment.forEach(eq => {
        const card = document.createElement('div');
        card.className = 'equipment-card';
        
        const skillsHtml = Object.entries(eq.skills)
            .map(([skill, level]) => `<span class="skill-item">${skill}(+${level})</span>`)
            .join('');
        
        card.innerHTML = `
            <div class="equipment-card-position">${eq.position}</div>
            <div class="equipment-card-title">${eq.name}</div>
            <div class="equipment-card-skills">
                ${skillsHtml || '<em>無技能加成</em>'}
            </div>
        `;
        grid.appendChild(card);
    });
}

// 更新頁面信息
function updatePageInfo(data) {
    const pageInfo = document.getElementById('pageInfo');
    const equipmentCount = document.getElementById('equipmentCount');
    
    pageInfo.textContent = `第 ${data.page} / ${data.pages} 頁`;
    equipmentCount.textContent = `共 ${data.total} 件裝備`;
}

// 上一頁
function previousPage() {
    if (state.currentPage > 1) {
        state.currentPage--;
        loadEquipmentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 下一頁
function nextPage() {
    if (state.currentPage < state.totalPages) {
        state.currentPage++;
        loadEquipmentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 加載配置
function loadConfig(configName) {
    fetch(`/api/config/${configName}`)
        .then(response => response.json())
        .then(data => {
            displayConfig(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加載配置失敗');
        });
}

// 顯示配置
function displayConfig(data) {
    const configContent = document.getElementById('configContent');
    configContent.innerHTML = `<h3>${data.name}</h3>`;
    
    Object.entries(data.config).forEach(([position, equipment]) => {
        if (equipment && equipment.length > 0) {
            const positionDiv = document.createElement('div');
            positionDiv.className = 'config-position';
            
            let html = `<div class="config-position-title">${position}</div>`;
            
            equipment.forEach(eq => {
                if (eq) {
                    const skillsStr = Object.entries(eq.skills)
                        .map(([skill, level]) => `${skill}(+${level})`)
                        .join(', ') || '無技能加成';
                    
                    html += `
                        <div class="config-item">
                            <span class="config-item-name">${eq.name}</span>
                            <span class="config-item-skills">${skillsStr}</span>
                        </div>
                    `;
                }
            });
            
            positionDiv.innerHTML = html;
            configContent.appendChild(positionDiv);
        }
    });
    
    configContent.style.display = 'block';
}

// 加載統計信息
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            displayStats(data);
        })
        .catch(error => console.error('Error loading stats:', error));
}

// 顯示統計信息
function displayStats(stats) {
    const statsContent = document.getElementById('statsContent');
    
    let html = `
        <div class="stat-card">
            <div class="stat-card-label">總裝備數</div>
            <div class="stat-card-value">${stats.total_equipment}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-label">位置類型</div>
            <div class="stat-card-value">${stats.positions.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-label">技能種類</div>
            <div class="stat-card-value">${stats.skills.length}</div>
        </div>
    `;
    
    statsContent.innerHTML = html;
    
    // 添加按位置的統計列表
    const listDiv = document.createElement('div');
    listDiv.className = 'stat-list';
    listDiv.innerHTML = '<h3>各位置的裝備數</h3>';
    
    const listContent = document.createElement('div');
    Object.entries(stats.equipment_by_position).forEach(([pos, count]) => {
        const item = document.createElement('div');
        item.className = 'stat-list-item';
        item.innerHTML = `<span>${pos}</span><strong>${count} 件</strong>`;
        listContent.appendChild(item);
    });
    
    listDiv.appendChild(listContent);
    statsContent.appendChild(listDiv);
}
