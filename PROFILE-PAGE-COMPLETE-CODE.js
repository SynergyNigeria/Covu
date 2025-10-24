// ========================================
// PROFILE PAGE - BACKEND INTEGRATION
// Complete Working Code - Copy this to profile.js
// ========================================

let currentUser = null;
let userStores = [];
let userOrders = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!api.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }
    lucide.createIcons();
    await loadUserProfile();
    await Promise.all([loadUserStores(), loadUserOrders()]);
    setupEventListeners();
});

async function loadUserProfile() {
    try {
        showLoadingState();
        const response = await api.get(API_CONFIG.ENDPOINTS.PROFILE);
        console.log('Profile response:', response);
        
        if (response && (response.id || response.email)) {
            currentUser = response;
        } else if (response.success && response.data) {
            currentUser = response.data;
        } else if (response.user) {
            currentUser = response.user;
        } else {
            throw new Error('Invalid profile response');
        }
        
        console.log('Current user:', currentUser);
        populateProfileData(currentUser);
    } catch (error) {
        console.error('Error loading profile:', error);
        showToast('Failed to load profile data', 'error');
        const storedUser = localStorage.getItem(API_CONFIG.TOKEN_KEYS.USER);
        if (storedUser) {
            try {
                currentUser = JSON.parse(storedUser);
                populateProfileData(currentUser);
            } catch (e) {
                console.error('Error parsing stored user:', e);
            }
        }
    } finally {
        hideLoadingState();
    }
}

function populateProfileData(user) {
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const userPhone = document.getElementById('userPhone');
    
    if (userName) userName.textContent = user.full_name || 'User';
    if (userEmail) {
        userEmail.innerHTML = `<i data-lucide="mail" class="h-4 w-4"></i> ${user.email || 'No email'}`;
    }
    if (userPhone) {
        userPhone.innerHTML = `<i data-lucide="phone" class="h-4 w-4"></i> ${user.phone_number || 'No phone'}`;
    }
    
    updateQuickStats(user);
    
    const contactEmail = document.getElementById('contactEmail');
    const contactPhone = document.getElementById('contactPhone');
    if (contactEmail) contactEmail.value = user.email || '';
    if (contactPhone) contactPhone.value = user.phone_number || '';
    
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');
    if (cityInput) cityInput.value = user.city || '';
    if (stateInput) stateInput.value = user.state || '';
    
    lucide.createIcons();
}

function updateQuickStats(user) {
    const statsContainer = document.querySelector('.flex.items-center.gap-6.mt-4');
    if (statsContainer) {
        const walletBalance = user.wallet_balance || 0;
        const ordersCount = userOrders.length || 0;
        const storesCount = userStores.length || 0;
        
        statsContainer.innerHTML = `
            <div class="text-center">
                <div class="text-xl font-bold">${formatCurrency(walletBalance)}</div>
                <div class="text-xs text-white/70">Wallet Balance</div>
            </div>
            <div class="text-center">
                <div class="text-xl font-bold">${ordersCount}</div>
                <div class="text-xs text-white/70">Orders</div>
            </div>
            ${user.is_seller ? `
                <div class="text-center">
                    <div class="text-xl font-bold">${storesCount}</div>
                    <div class="text-xs text-white/70">Stores</div>
                </div>
            ` : `
                <div class="text-center">
                    <div class="text-xl font-bold">${user.is_seller ? 'Seller' : 'Buyer'}</div>
                    <div class="text-xs text-white/70">Account Type</div>
                </div>
            `}
        `;
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
        minimumFractionDigits: 0
    }).format(amount);
}

async function loadUserStores() {
    if (!currentUser || !currentUser.is_seller) {
        updateShopStatus(false, null);
        return;
    }
    
    try {
        const response = await api.get(API_CONFIG.ENDPOINTS.STORES);
        console.log('Stores response:', response);
        
        let stores = [];
        if (response.success && response.data && response.data.results) {
            stores = response.data.results;
        } else if (response.results) {
            stores = response.results;
        } else if (Array.isArray(response)) {
            stores = response;
        }
        
        userStores = stores.filter(store => store.seller_id === currentUser.id || store.seller === currentUser.id);
        console.log('User stores:', userStores);
        
        if (userStores.length > 0) {
            updateShopStatus(true, userStores[0]);
        } else {
            updateShopStatus(false, null);
        }
    } catch (error) {
        console.error('Error loading stores:', error);
        updateShopStatus(false, null);
    }
}

function updateShopStatus(hasStore, store) {
    const shopStatus = document.getElementById('shopStatus');
    const shopActionBtn = document.getElementById('shopActionBtn');
    
    if (!shopStatus || !shopActionBtn) return;
    
    if (hasStore && store) {
        shopStatus.textContent = `Active: ${store.name}`;
        shopActionBtn.textContent = 'View Shop';
        shopActionBtn.className = 'px-6 py-2 bg-gradient-to-r from-primary-green to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5';
        shopActionBtn.onclick = () => {
            window.location.href = `shop.html?store_id=${store.id}`;
        };
    } else {
        shopStatus.textContent = currentUser && currentUser.is_seller ? 'No active shop' : 'Not a seller';
        shopActionBtn.textContent = currentUser && currentUser.is_seller ? 'Create Shop' : 'Become a Seller';
        shopActionBtn.className = 'px-6 py-2 bg-gradient-to-r from-primary-orange to-orange-500 text-white rounded-lg hover:from-orange-500 hover:to-orange-600 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5';
        shopActionBtn.onclick = () => {
            showToast('Shop creation feature coming soon!', 'info');
        };
    }
}

async function loadUserOrders() {
    try {
        const response = await api.get(API_CONFIG.ENDPOINTS.ORDERS);
        console.log('Orders response:', response);
        
        if (response.success && response.data && response.data.results) {
            userOrders = response.data.results;
        } else if (response.results) {
            userOrders = response.results;
        } else if (Array.isArray(response)) {
            userOrders = response;
        } else {
            userOrders = [];
        }
        
        console.log('User orders:', userOrders);
    } catch (error) {
        console.error('Error loading orders:', error);
        userOrders = [];
    }
}

function setupEventListeners() {
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) passwordForm.addEventListener('submit', handlePasswordUpdate);
    
    const locationForm = document.getElementById('locationForm');
    if (locationForm) locationForm.addEventListener('submit', handleLocationUpdate);
    
    const contactForm = document.getElementById('contactForm');
    if (contactForm) contactForm.addEventListener('submit', handleContactUpdate);
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
}

async function handlePasswordUpdate(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword');
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    
    if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
        showToast('Please fill in all password fields', 'error');
        return;
    }
    
    if (newPassword.value !== confirmPassword.value) {
        showToast('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword.value.length < 8) {
        showToast('Password must be at least 8 characters long', 'error');
        return;
    }
    
    try {
        showButtonLoading(e.submitter);
        
        const response = await api.post('/auth/password/change/', {
            old_password: currentPassword.value,
            new_password: newPassword.value,
            new_password_confirm: confirmPassword.value
        });
        
        console.log('Password change response:', response);
        
        if (response.success || response.message) {
            showToast('Password updated successfully! Please login again.', 'success');
            e.target.reset();
            setTimeout(() => handleLogout(), 2000);
        } else {
            throw new Error(response.message || 'Failed to update password');
        }
    } catch (error) {
        console.error('Error updating password:', error);
        const errorMsg = error.response?.data?.old_password?.[0] || 
                        error.response?.data?.new_password?.[0] ||
                        error.message || 
                        'Failed to update password';
        showToast(errorMsg, 'error');
    } finally {
        hideButtonLoading(e.submitter);
    }
}

async function handleLocationUpdate(e) {
    e.preventDefault();
    
    const city = document.getElementById('city').value.trim();
    const state = document.getElementById('state').value.trim();
    
    if (!city || !state) {
        showToast('Please fill in all location fields', 'error');
        return;
    }
    
    try {
        showButtonLoading(e.submitter);
        
        const response = await api.patch(API_CONFIG.ENDPOINTS.PROFILE, {
            city: city,
            state: state
        });
        
        console.log('Location update response:', response);
        
        if (response.success || response.message || response.user) {
            showToast('Location updated successfully!', 'success');
            
            if (response.user) {
                currentUser = response.user;
                populateProfileData(currentUser);
            } else if (response.data) {
                currentUser = response.data;
                populateProfileData(currentUser);
            }
            
            localStorage.setItem(API_CONFIG.TOKEN_KEYS.USER, JSON.stringify(currentUser));
        } else {
            throw new Error('Failed to update location');
        }
    } catch (error) {
        console.error('Error updating location:', error);
        showToast(error.message || 'Failed to update location', 'error');
    } finally {
        hideButtonLoading(e.submitter);
    }
}

async function handleContactUpdate(e) {
    e.preventDefault();
    
    const phone = document.getElementById('contactPhone').value.trim();
    
    if (!phone) {
        showToast('Please enter a phone number', 'error');
        return;
    }
    
    try {
        showButtonLoading(e.submitter);
        
        const response = await api.patch(API_CONFIG.ENDPOINTS.PROFILE, {
            phone_number: phone
        });
        
        console.log('Contact update response:', response);
        
        if (response.success || response.message || response.user) {
            showToast('Contact information updated successfully!', 'success');
            
            if (response.user) {
                currentUser = response.user;
                populateProfileData(currentUser);
            } else if (response.data) {
                currentUser = response.data;
                populateProfileData(currentUser);
            }
            
            localStorage.setItem(API_CONFIG.TOKEN_KEYS.USER, JSON.stringify(currentUser));
        } else {
            throw new Error('Failed to update contact information');
        }
    } catch (error) {
        console.error('Error updating contact:', error);
        const errorMsg = error.response?.data?.phone_number?.[0] || 
                        error.message || 
                        'Failed to update contact information';
        showToast(errorMsg, 'error');
    } finally {
        hideButtonLoading(e.submitter);
    }
}

function handleLogout() {
    if (confirm('Are you sure you want to log out?')) {
        localStorage.removeItem(API_CONFIG.TOKEN_KEYS.ACCESS);
        localStorage.removeItem(API_CONFIG.TOKEN_KEYS.REFRESH);
        localStorage.removeItem(API_CONFIG.TOKEN_KEYS.USER);
        showToast('Logged out successfully!', 'success');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1000);
    }
}

function showLoadingState() {
    const userName = document.getElementById('userName');
    if (userName) userName.textContent = 'Loading...';
}

function hideLoadingState() {}

function showButtonLoading(button) {
    if (!button) return;
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.innerHTML = `<div class="flex items-center justify-center gap-2"><svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Processing...</span></div>`;
}

function hideButtonLoading(button) {
    if (!button) return;
    button.disabled = false;
    button.textContent = button.dataset.originalText || 'Submit';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    if (!toast || !toastMessage) return;
    
    toastMessage.textContent = message;
    
    const colors = {
        success: 'bg-primary-green',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };
    
    toast.className = `fixed top-4 right-4 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm ${colors[type] || colors.success}`;
    toast.classList.remove('hidden');
    lucide.createIcons();
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
