/**
 * AI Daily News - 简洁科技风前端
 */

const CONFIG = {
    dataPath: '../data',
    indexFile: 'index.json',
    dailyPath: 'daily'
};

let state = {
    currentDate: null,
    dates: [],
    statistics: null,
    charts: {}
};

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadIndex();
        if (state.dates.length > 0) {
            await loadDailyNews(state.dates[0]);
        }
    } catch (error) {
        console.error('初始化失败:', error);
        loadDemoData();
    }
});

// 加载索引
async function loadIndex() {
    try {
        const response = await fetch(`${CONFIG.dataPath}/${CONFIG.indexFile}`);
        if (!response.ok) throw new Error('索引不存在');
        
        const data = await response.json();
        state.dates = data.dates || [];
        state.statistics = data.statistics || {};
        
        renderDateList();
        document.getElementById('update-time').textContent = 
            `最后更新: ${data.last_updated || '--'}`;
    } catch (error) {
        throw error;
    }
}

// 渲染日期列表
function renderDateList() {
    const container = document.getElementById('date-list');
    
    if (state.dates.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无数据</div>';
        return;
    }
    
    container.innerHTML = state.dates.map((date, index) => {
        const d = new Date(date);
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return `
            <div class="date-item ${index === 0 ? 'active' : ''}" data-date="${date}">
                <span class="date-main">${d.getMonth() + 1}月${d.getDate()}日</span>
                <span class="date-sub">${weekdays[d.getDay()]}</span>
            </div>
        `;
    }).join('');
    
    // 绑定点击事件
    container.querySelectorAll('.date-item').forEach(item => {
        item.addEventListener('click', () => {
            container.querySelectorAll('.date-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            loadDailyNews(item.dataset.date);
        });
    });
}

// 加载每日新闻
async function loadDailyNews(date) {
    state.currentDate = date;
    
    // 显示加载状态
    document.getElementById('domestic-news').innerHTML = '<div class="loading-text">加载中...</div>';
    document.getElementById('international-news').innerHTML = '<div class="loading-text">加载中...</div>';
    
    try {
        const response = await fetch(`${CONFIG.dataPath}/${CONFIG.dailyPath}/${date}.json`);
        if (!response.ok) throw new Error('数据不存在');
        
        const data = await response.json();
        
        // 更新标题
        const d = new Date(date);
        document.getElementById('current-date').textContent = 
            `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 AI动态`;
        
        // 更新统计
        document.getElementById('stat-domestic').textContent = data.domestic?.length || 0;
        document.getElementById('stat-international').textContent = data.international?.length || 0;
        document.getElementById('total-news').textContent = 
            (data.domestic?.length || 0) + (data.international?.length || 0);
        document.getElementById('raw-news').textContent = 
            data.statistics?.raw_total || '--';
        
        // 渲染新闻
        renderNews('domestic-news', data.domestic || []);
        renderNews('international-news', data.international || []);
        
        // 更新图表
        updateCharts(data);
        
    } catch (error) {
        console.error('加载失败:', error);
        document.getElementById('domestic-news').innerHTML = '<div class="empty-state">暂无数据</div>';
        document.getElementById('international-news').innerHTML = '<div class="empty-state">暂无数据</div>';
    }
}

// 渲染新闻列表
function renderNews(containerId, newsList) {
    const container = document.getElementById(containerId);
    
    if (!newsList || newsList.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无动态</div>';
        return;
    }
    
    container.innerHTML = newsList.map(news => {
        const isHigh = news.importance === '高';
        // 提取核心摘要内容
        let summary = news.summary || '';
        // 确保格式正确
        if (!summary.includes('消息，')) {
            const d = new Date(state.currentDate);
            summary = `${d.getMonth() + 1}月${d.getDate()}日消息，${summary}`;
        }
        
        return `
            <div class="news-item ${isHigh ? 'high' : ''}">
                <span class="news-index">${news.index}</span>
                <div class="news-content">
                    <p class="news-text">${escapeHtml(summary)}</p>
                    ${news.url ? `<div class="news-meta"><a href="${news.url}" target="_blank">查看原文 →</a></div>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// 更新图表
function updateCharts(data) {
    // 分类占比饼图
    const categoryCtx = document.getElementById('category-chart');
    if (state.charts.category) state.charts.category.destroy();
    
    state.charts.category = new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: ['国内', '国际'],
            datasets: [{
                data: [data.domestic?.length || 0, data.international?.length || 0],
                backgroundColor: ['#0066ff', '#6c757d'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        boxWidth: 12,
                        padding: 8,
                        font: { size: 11 }
                    }
                }
            },
            cutout: '60%'
        }
    });
    
    // 重要性分布
    const importanceCtx = document.getElementById('importance-chart');
    if (state.charts.importance) state.charts.importance.destroy();
    
    const allNews = [...(data.domestic || []), ...(data.international || [])];
    const highCount = allNews.filter(n => n.importance === '高').length;
    const mediumCount = allNews.filter(n => n.importance === '中').length;
    const lowCount = allNews.filter(n => n.importance === '低').length;
    
    state.charts.importance = new Chart(importanceCtx, {
        type: 'doughnut',
        data: {
            labels: ['高', '中', '低'],
            datasets: [{
                data: [highCount, mediumCount, lowCount],
                backgroundColor: ['#dc3545', '#ffc107', '#28a745'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        boxWidth: 12,
                        padding: 8,
                        font: { size: 11 }
                    }
                }
            },
            cutout: '60%'
        }
    });
    
    // 趋势图
    const trendCtx = document.getElementById('trend-chart');
    if (state.charts.trend) state.charts.trend.destroy();
    
    const byDate = state.statistics?.by_date?.slice(0, 7).reverse() || [];
    
    state.charts.trend = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: byDate.map(d => {
                const date = new Date(d.date);
                return `${date.getMonth() + 1}/${date.getDate()}`;
            }),
            datasets: [
                {
                    label: '国内',
                    data: byDate.map(d => d.domestic || 0),
                    borderColor: '#0066ff',
                    backgroundColor: 'rgba(0,102,255,0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3
                },
                {
                    label: '国际',
                    data: byDate.map(d => d.international || 0),
                    borderColor: '#6c757d',
                    backgroundColor: 'rgba(108,117,125,0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        boxWidth: 12,
                        padding: 8,
                        font: { size: 11 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f0f0f0' },
                    ticks: { 
                        font: { size: 10 },
                        stepSize: 5
                    }
                }
            }
        }
    });
}

// 加载演示数据
function loadDemoData() {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    const month = today.getMonth() + 1;
    const day = today.getDate();
    
    state.dates = [dateStr];
    state.statistics = {
        by_date: [{ date: dateStr, domestic: 10, international: 12 }]
    };
    
    renderDateList();
    document.getElementById('update-time').textContent = '演示数据';
    
    const demoData = {
        domestic: [
            { index: 1, importance: '高', summary: `${month}月${day}日消息，智谱AI宣布开源AutoGLM项目，经过32个月研发构建完整Phone Use能力框架，使AI能通过视觉理解手机界面完成点击、滑动等操作，实现外卖下单、批量处理通知等自动化任务，系统主要在云端虚拟手机环境运行以保障隐私安全。` },
            { index: 2, importance: '高', summary: `${month}月${day}日消息，蚂蚁集团正式推出全模态通用AI助手灵光网页版，延续"30秒用自然语言生成小应用"核心优势，实现与移动端数据创作同步。` },
            { index: 3, importance: '高', summary: `${month}月${day}日消息，百度宣布文心一言升级至4.5版本，在代码生成、数学推理等方面性能大幅提升，API调用成本降低60%，用户数突破3亿。` },
            { index: 4, importance: '中', summary: `${month}月${day}日消息，华为发布新一代昇腾910C AI训练芯片，算力达到640 TFLOPS，较上代提升80%，将大规模应用于国产AI服务器。` },
            { index: 5, importance: '中', summary: `${month}月${day}日消息，阿里云宣布开源通义千问Qwen2.5-Max模型，1100亿参数版本在代码生成、数学推理任务上达到业界领先水平。` }
        ],
        international: [
            { index: 1, importance: '高', summary: `${month}月${day}日消息，据美国多家媒体证实，美国总统特朗普宣布允许英伟达向中国出售H200人工智能芯片，但要求英伟达将25%的收益支付给美国政府。H200性能约为H20的6-13倍，但仍落后于最新的Blackwell架构。此项政策同样适用于AMD、英特尔等其他美国芯片公司，商务部正在敲定相关细节。` },
            { index: 2, importance: '高', summary: `${month}月${day}日消息，OpenAI正式发布GPT-5大语言模型，采用全新混合架构，在推理、编程、多模态理解等方面实现重大突破，上下文窗口扩展至100万tokens。` },
            { index: 3, importance: '高', summary: `${month}月${day}日消息，欧盟《人工智能法案》正式全面生效，成为全球首部全面监管AI的立法，高风险AI系统需在6个月内完成合规，违规企业将面临最高3500万欧元罚款。` },
            { index: 4, importance: '中', summary: `${month}月${day}日消息，谷歌DeepMind发布Gemini 2.5 Ultra多模态大模型，在数学、科学推理、代码生成等任务上超越GPT-5基准版。` },
            { index: 5, importance: '中', summary: `${month}月${day}日消息，Meta正式开源Llama 4系列模型，包含8B到400B多个规格，采用混合专家架构，24小时内下载量突破100万次。` }
        ],
        statistics: { raw_total: 113 }
    };
    
    document.getElementById('current-date').textContent = 
        `${today.getFullYear()}年${month}月${day}日 AI动态`;
    document.getElementById('stat-domestic').textContent = demoData.domestic.length;
    document.getElementById('stat-international').textContent = demoData.international.length;
    document.getElementById('total-news').textContent = 
        demoData.domestic.length + demoData.international.length;
    document.getElementById('raw-news').textContent = demoData.statistics.raw_total;
    
    renderNews('domestic-news', demoData.domestic);
    renderNews('international-news', demoData.international);
    updateCharts(demoData);
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
