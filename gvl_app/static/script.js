// GVL 裝備表前端 JavaScript

// 全局狀態
let state = {
    currentPage: 1,
    perPage: 20,
    totalPages: 1,
    characterOptions: null
};

const CHARACTER_SLOT_SIDE_ORDER = [
    ['飾品1', 'left'],
    ['飾品2', 'left'],
    ['寶物1', 'left'],
    ['寶物2', 'left'],
    ['主武', 'left'],
    ['副武', 'left'],
    ['頭盔', 'right'],
    ['衣服', 'right'],
    ['手套', 'right'],
    ['鞋子', 'right']
];
const CHARACTER_SLOT_SIDE_MAP = Object.fromEntries(CHARACTER_SLOT_SIDE_ORDER);
const CHARACTER_DUPLICATE_POSITIONS = new Set(['飾品', '寶物']);
const DEFAULT_SLOT_SIDE = 'right';
const DUPLICATE_SLOT_COUNT = 2;

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化頁面
function initializePage() {
    loadPositions();
    loadSkills();
    loadEquipmentPage();
    loadCharacterOptions();
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

// 加載角色配裝選項
function loadCharacterOptions() {
    fetch('/api/character/options')
        .then(response => response.json())
        .then(data => {
            state.characterOptions = data;
            renderProfessionOptions(data.professions);
            renderCharacterEquipmentForm(data.equipment_by_position);
            renderSailorSkillsHint(data.sailor_skills || []);
        })
        .catch(error => console.error('Error loading character options:', error));
}

/**
 * 顯示航海士可加成技能提示
 * @param {string[]} sailorSkills 航海士可加成技能列表
 */
function renderSailorSkillsHint(sailorSkills) {
    const hint = document.getElementById('sailorSkillsHint');
    if (!hint) {
        return;
    }

    if (!sailorSkills.length) {
        hint.innerHTML = '<em>未設定航海士可加成技能</em>';
        return;
    }

    const skillsText = sailorSkills.map(skill => escapeHtml(skill)).join('、');
    hint.innerHTML = `<small>航海士可加成技能：${skillsText}</small>`;
}

/**
 * 將技能映射轉為 HTML 標籤集合
 * @param {Object<string, number>} skills 技能與數值映射
 * @param {boolean} withPlus 是否以 +x 顯示數值
 * @param {string} emptyText 空資料時顯示文字
 * @returns {string} 技能 HTML 內容
 */
function renderSkillItems(skills, withPlus = false, emptyText = '無') {
    const entries = Object.entries(skills || {});
    if (!entries.length) {
        return `<em>${escapeHtml(emptyText)}</em>`;
    }
    return entries
        .map(([skill, level]) => {
            const valueText = withPlus
                ? `+${escapeHtml(level)}`
                : `${escapeHtml(level)}`;
            const highClass = level >= 25 ? ' skill-item--high' : '';
            return `<span class="skill-item${highClass}">${escapeHtml(skill)}(${valueText})</span>`;
        })
        .join('');
}

/**
 * 顯示職業選項
 * @param {Object<string, Object<string, number>>} professions 職業與技能加成映射
 */
function renderProfessionOptions(professions) {
    const select = document.getElementById('professionSelect');
    select.innerHTML = '';

    Object.keys(professions).forEach(profession => {
        const option = document.createElement('option');
        option.value = profession;
        option.textContent = profession;
        select.appendChild(option);
    });
}

/**
 * 顯示配裝選單
 * @param {Object<string, string[]>} equipmentByPosition 位置與裝備名稱列表映射
 */
function renderCharacterEquipmentForm(equipmentByPosition) {
    const leftColumn = document.getElementById('characterLeftSlots');
    const rightColumn = document.getElementById('characterRightSlots');

    if (!leftColumn || !rightColumn) {
        return;
    }

    leftColumn.innerHTML = '';
    rightColumn.innerHTML = '';

    const slotPlan = buildCharacterSlotPlan(equipmentByPosition);

    slotPlan.forEach(slot => {
        const group = document.createElement('div');
        group.className = 'character-slot';

        const label = document.createElement('label');
        label.className = 'character-slot-label';
        label.textContent = slot.label;

        const select = document.createElement('select');
        select.className = 'search-input';
        select.dataset.position = slot.position;

        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '不裝備';
        select.appendChild(emptyOption);

        slot.equipmentNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            select.appendChild(option);
        });

        group.appendChild(label);
        group.appendChild(select);

        if (slot.side === 'right') {
            rightColumn.appendChild(group);
            return;
        }
        leftColumn.appendChild(group);
    });

    setupCharacterAutoCalculate();
}

/**
 * 為職業選單、航海士勾選框與所有裝備下拉選單綁定 change 事件，
 * 讓技能結果在選項變更時即時重新計算。
 */
function setupCharacterAutoCalculate() {
    document.querySelectorAll('#characterEquipmentForm select').forEach(select => {
        select.addEventListener('change', calculateCharacterSkills);
    });

    const professionSelect = document.getElementById('professionSelect');
    if (professionSelect) {
        professionSelect.addEventListener('change', calculateCharacterSkills);
    }

    const sailorCheckbox = document.getElementById('sailorCheckbox');
    if (sailorCheckbox) {
        sailorCheckbox.addEventListener('change', calculateCharacterSkills);
    }
}

/**
 * 建立角色配裝欄位配置，讓版面接近建議 UI 圖
 * @param {Object<string, string[]>} equipmentByPosition 位置與裝備名稱列表
 * @returns {Array<{position: string, label: string, equipmentNames: string[], side: string}>}
 */
function buildCharacterSlotPlan(equipmentByPosition) {
    const slots = [];

    Object.entries(equipmentByPosition).forEach(([position, equipmentNames]) => {
        const copyCount = CHARACTER_DUPLICATE_POSITIONS.has(position) ? DUPLICATE_SLOT_COUNT : 1;
        for (let i = 1; i <= copyCount; i++) {
            const slotName = copyCount > 1 ? `${position}${i}` : position;
            slots.push({
                position,
                label: slotName,
                equipmentNames: equipmentNames || [],
                side: CHARACTER_SLOT_SIDE_MAP[slotName]
                    || CHARACTER_SLOT_SIDE_MAP[position]
                    || DEFAULT_SLOT_SIDE
            });
        }
    });

    return slots.sort((a, b) => {
        const aIndex = CHARACTER_SLOT_SIDE_ORDER.findIndex(([slotName]) => slotName === a.label);
        const bIndex = CHARACTER_SLOT_SIDE_ORDER.findIndex(([slotName]) => slotName === b.label);
        if (aIndex !== bIndex) {
            return (aIndex === -1 ? Number.MAX_SAFE_INTEGER : aIndex)
                - (bIndex === -1 ? Number.MAX_SAFE_INTEGER : bIndex);
        }
        return a.label.localeCompare(b.label, 'zh-Hant');
    });
}

/**
 * 收集角色配裝資料並呼叫 API 計算技能
 */
function calculateCharacterSkills() {
    const profession = document.getElementById('professionSelect').value;
    const isSailor = document.getElementById('sailorCheckbox')?.checked || false;
    const equipmentNames = [];

    document.querySelectorAll('#characterEquipmentForm select').forEach(select => {
        if (select.value) {
            equipmentNames.push(select.value);
        }
    });

    fetch('/api/character/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            profession,
            equipment_names: equipmentNames,
            is_sailor: isSailor
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            displayCharacterResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('計算角色技能失敗');
        });
}

/**
 * 顯示角色技能計算結果
 * @param {Object} data 計算結果資料
 */
function displayCharacterResults(data) {
    const container = document.getElementById('characterResults');
    const content = document.getElementById('characterResultsContent');
    const wasHidden = container.style.display === 'none';

    const skillCapsHtml = renderSkillItems(data.skill_caps, false, '未設定角色技能上限');
    const equipmentBonusHtml = renderSkillItems(data.equipment_skills, true, '目前沒有裝備技能加成');
    const professionBonusHtml = renderSkillItems(data.profession_bonus, true, '此職業無額外技能加成');
    const sailorBonusHtml = renderSkillItems(data.sailor_bonus, true, '未啟用航海士加成');
    const highestSkillsHtml = renderSkillItems(data.highest_skills, false, '目前沒有技能加成');

    const selectedEquipmentHtml = data.selected_equipment
        .map(eq => `<li>${escapeHtml(eq.position)}：${escapeHtml(eq.name)}</li>`)
        .join('') || '<li>尚未選擇裝備</li>';

    const invalidEquipmentHtml = (data.invalid_equipment || [])
        .map(name => `<li>${escapeHtml(name)}</li>`)
        .join('');

    content.innerHTML = `
        <div class="character-summary">
            <div><strong>職業：</strong>${escapeHtml(data.profession)}</div>
            <div><strong>航海士：</strong>${data.is_sailor ? '是' : '否'}</div>
            <div><strong>已選裝備：</strong></div>
            <ul>${selectedEquipmentHtml}</ul>
            ${invalidEquipmentHtml ? `<div><strong>未找到裝備：</strong><ul>${invalidEquipmentHtml}</ul></div>` : ''}
        </div>
        <div class="character-skills-block">
            <h4>角色技能上限</h4>
            <div>${skillCapsHtml}</div>
        </div>
        <div class="character-skills-block">
            <h4>裝備技能加成（+x）</h4>
            <div>${equipmentBonusHtml}</div>
        </div>
        <div class="character-skills-block">
            <h4>職業技能加成</h4>
            <div>${professionBonusHtml}</div>
        </div>
        <div class="character-skills-block">
            <h4>航海士技能加成</h4>
            <div>${sailorBonusHtml}</div>
        </div>
        <div class="character-skills-block">
            <h4>最高技能（角色上限 + 職業 + 裝備 + 航海士）</h4>
            <div>${highestSkillsHtml}</div>
        </div>
    `;

    container.style.display = 'block';
    if (wasHidden) {
        container.scrollIntoView({ behavior: 'smooth' });
    }
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
