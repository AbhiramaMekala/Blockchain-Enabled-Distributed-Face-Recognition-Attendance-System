async function loadAttendance() {
    try {
      const res = await fetch('/api/attendance/latest');
      const data = await res.json();
  
      const tbody = document.querySelector('#attendance-table tbody');
      tbody.innerHTML = '';
  
      data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${item.name}</td>
          <td class="${item.status.toLowerCase()}">${item.status}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error('Error loading attendance', err);
    }
  }
  
  document.getElementById('refresh-btn').addEventListener('click', loadAttendance);
  
  // Auto-refresh every 5 seconds
  setInterval(loadAttendance, 5000);
  
  // Initial load
  loadAttendance();
  