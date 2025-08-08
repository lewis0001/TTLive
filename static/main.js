const socket = io();

const connectBtn = document.getElementById('connect');
const disconnectBtn = document.getElementById('disconnect');
const usernameInput = document.getElementById('username');
const commentsList = document.getElementById('comments');
const viewerSpan = document.getElementById('viewerCount');
const likeSpan = document.getElementById('likeCount');
const shareSpan = document.getElementById('shareCount');
const leaderboardList = document.getElementById('leaderboard');
const battleTimerDiv = document.getElementById('battleTimer');

connectBtn.onclick = () => {
    const username = usernameInput.value.trim();
    if (username) {
        socket.emit('connect_stream', {username});
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
    }
};

disconnectBtn.onclick = () => {
    socket.emit('disconnect_stream');
};

socket.on('disconnected', () => {
    connectBtn.disabled = false;
    disconnectBtn.disabled = true;
    commentsList.innerHTML = '';
    viewerSpan.innerText = 0;
    likeSpan.innerText = 0;
    shareSpan.innerText = 0;
    leaderboardList.innerHTML = '';
    battleTimerDiv.innerText = '';
});

socket.on('comment', data => {
    const li = document.createElement('li');
    if (data.avatar) {
        const img = document.createElement('img');
        img.src = data.avatar;
        img.width = 30;
        img.height = 30;
        li.appendChild(img);
    }
    li.append(` ${data.nickname}: ${data.comment}`);
    commentsList.prepend(li);
});

socket.on('viewer', data => {
    viewerSpan.innerText = data.count;
});

socket.on('like', data => {
    likeSpan.innerText = data.total;
});

socket.on('share', data => {
    shareSpan.innerText = data.count;
});

socket.on('gift', data => {
    const li = document.createElement('li');
    li.textContent = `${data.nickname} sent ${data.count} x ${data.gift}`;
    commentsList.prepend(li);
});

socket.on('leaderboard', data => {
    leaderboardList.innerHTML = '';
    Object.entries(data).sort((a, b) => b[1] - a[1]).forEach(([name, value]) => {
        const li = document.createElement('li');
        li.textContent = `${name}: ${value}`;
        leaderboardList.appendChild(li);
    });
});

socket.on('battle', data => {
    battleTimerDiv.innerText = JSON.stringify(data);
});

socket.on('end', () => {
    battleTimerDiv.innerText = 'Live ended';
});
