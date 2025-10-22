/**
 * Test script to verify session expiration handling
 * This script can be run in the browser console to test the auth error handling
 */

// Test function to simulate a 401 error
function testSessionExpiration() {
  console.log('Testing session expiration handling...');
  
  // Simulate a 401 error by calling the auth error handler directly
  const { handleAuthError } = require('@/utils/authErrorHandler');
  
  console.log('Before calling handleAuthError:');
  console.log('isAuthenticated:', localStorage.getItem('access_token') ? 'true' : 'false');
  console.log('Current URL:', window.location.href);
  
  // Call the auth error handler
  handleAuthError();
  
  console.log('After calling handleAuthError:');
  console.log('isAuthenticated:', localStorage.getItem('access_token') ? 'true' : 'false');
  console.log('Current URL:', window.location.href);
}

// Test function to verify API interceptor behavior
function testApiInterceptor() {
  console.log('Testing API interceptor behavior...');
  
  // This would normally be called by axios interceptors
  // We can simulate it by making a request that returns 401
  fetch('/api/v1/test-401', {
    headers: {
      'Authorization': `Bearer invalid-token`,
    },
  }).catch(error => {
    console.log('API call failed as expected:', error);
  });
}

// Export for use in browser console
if (typeof window !== 'undefined') {
  (window as any).testSessionExpiration = testSessionExpiration;
  (window as any).testApiInterceptor = testApiInterceptor;
}

export { testSessionExpiration, testApiInterceptor };
