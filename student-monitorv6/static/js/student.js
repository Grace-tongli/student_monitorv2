function startMonitoring() {
    const monitorMouse = document.getElementById('monitor-mouse').checked;
    const monitorKeyboard = document.getElementById('monitor-keyboard').checked;

    let type = 'all';
    if (monitorMouse && !monitorKeyboard) type = 'mouse';
    if (!monitorMouse && monitorKeyboard) type = 'keyboard';

    fetch('/api/start_monitoring', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type: type })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('监控已启动');
            location.reload();
        } else {
            alert('启动监控失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('启动监控时发生错误');
    });
}

function stopMonitoring() {
    fetch('/api/stop_monitoring', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message || '监控已停止');
            location.reload();
        } else {
            alert('停止监控失败: ' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('停止监控时发生网络错误');
    });
}

function showTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // 移除所有标签的活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的标签内容
    document.getElementById(`${tabName}-data`).style.display = 'block';

    // 设置选中的标签为活动状态
    event.target.classList.add('active');

    // 加载数据
    loadActivityData(tabName);
}

// 加载活动数据
function loadActivityData(dataType) {
    fetch(`/api/monitoring_data?type=${dataType}`)
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById(`${dataType}-data-body`);
        if (data.error) {
            container.innerHTML = `<tr><td colspan="3">${data.error}</td></tr>`;
        } else if (data.data && data.data.length > 0) {
            let html = '';
            data.data.forEach(item => {
                if (dataType === 'mouse') {
                    html += `<tr>
                        <td>${item.time}</td>
                        <td>${item.action}</td>
                        <td>${item.position}</td>
                    </tr>`;
                } else {
                    html += `<tr>
                        <td>${item.time}</td>
                        <td>${item.key}</td>
                        <td>${item.duration}</td>
                    </tr>`;
                }
            });
            container.innerHTML = html;
        } else {
            container.innerHTML = '<tr><td colspan="3">暂无活动数据</td></tr>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById(`${dataType}-data-body`).innerHTML = '<tr><td colspan="3">加载数据时发生错误</td></tr>';
    });
}

// 页面加载时获取数据
document.addEventListener('DOMContentLoaded', function() {
    // 初始加载鼠标数据
    loadActivityData('mouse');
});