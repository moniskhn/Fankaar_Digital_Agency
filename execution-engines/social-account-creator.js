const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * SOCIAL ACCOUNT CREATOR — CDP Automation
 * Uses Chrome DevTools Protocol to create social media accounts
 * for Fankaar Digital across all platforms.
 *
 * Requires:
 * - Chrome running with --remote-debugging-port=18690
 * - SMS verification API key (5sim.net or sms-activate.org)
 * - Email address for verification
 *
 * Run: node social-account-creator.js
 */

const CDP_URL = 'http://127.0.0.1:18690';
const AGENCY_NAME = 'Fankaar Digital';
const AGENCY_BIO = 'AI-powered marketing agency. 23 agents. 24/7 execution. Dubai \u00b7 Worldwide \u2192 fankaar.digital';

// Platform configurations
const PLATFORMS = {
    instagram: {
        signupUrl: 'https://www.instagram.com/accounts/emailsignup/',
        fields: {
            email: 'input[name="emailOrPhone"]',
            fullName: 'input[name="fullName"]',
            username: 'input[name="username"]',
            password: 'input[name="password"]'
        },
        submitButton: 'button[type="submit"]',
        username: 'fankaar.digital',
        needsPhone: true
    },
    linkedin: {
        signupUrl: 'https://www.linkedin.com/signup',
        fields: {
            email: 'input#email-address',
            password: 'input#password',
            firstName: 'input#first-name',
            lastName: 'input#last-name'
        },
        submitButton: 'button[type="submit"]',
        username: 'fankaar-digital',
        needsPhone: false
    },
    twitter: {
        signupUrl: 'https://twitter.com/i/flow/signup',
        fields: {
            name: 'input[name="name"]',
            phone: 'input[name="phone_number"]'
        },
        username: 'fankaardigital',
        needsPhone: true
    },
    tiktok: {
        signupUrl: 'https://www.tiktok.com/signup',
        fields: {},
        username: 'fankaar.digital',
        needsPhone: true
    }
};

async function connectToChrome() {
    console.log('[Account Creator] Connecting to Chrome CDP...');
    try {
        const browser = await puppeteer.connect({
            browserWSEndpoint: `ws://127.0.0.1:18690/devtools/browser`,
            defaultViewport: { width: 1280, height: 800 }
        });
        console.log('[Account Creator] Connected to Chrome');
        return browser;
    } catch (err) {
        console.error('[Account Creator] Failed to connect:', err.message);
        console.log('[Account Creator] Make sure Chrome is running with:');
        console.log('  Google Chrome --remote-debugging-port=18690');
        throw err;
    }
}

async function createInstagramAccount(browser) {
    console.log('\n[Instagram] Starting account creation...');
    const page = await browser.newPage();

    try {
        await page.goto('https://www.instagram.com/accounts/emailsignup/', { waitUntil: 'networkidle2', timeout: 30000 });
        console.log('[Instagram] Loaded signup page');

        // Wait for and fill the form
        await page.waitForSelector('input[name="emailOrPhone"]', { timeout: 10000 });

        // Use email instead of phone to avoid SMS verification
        await page.type('input[name="emailOrPhone"]', 'fankaar.social@gmail.com', { delay: 50 });
        await page.type('input[name="fullName"]', 'Fankaar Digital', { delay: 50 });

        // Instagram auto-generates username, we'll change it later
        await page.type('input[name="password"]', generateSecurePassword(), { delay: 50 });

        // Click next
        await page.click('button[type="submit"]');
        console.log('[Instagram] Submitted initial form');

        // Wait for birthday page
        await page.waitForTimeout(2000);

        // Fill birthday (make it realistic)
        await page.select('select[title="Day:"]', '15');
        await page.select('select[title="Month:"]', '6'); // June
        await page.select('select[title="Year:"]', '1995');

        await page.click('button[type="submit"]');
        console.log('[Instagram] Submitted birthday');

        // Wait for confirmation code page
        await page.waitForTimeout(3000);

        // At this point, Instagram sends a confirmation code to email
        console.log('[Instagram] Waiting for email verification...');
        console.log('[Instagram] Check fankaar.social@gmail.com for code');

        // Save screenshot for debugging
        await page.screenshot({ path: '/tmp/instagram-signup-status.png' });

        console.log('[Instagram] Account creation initiated. Manual step needed: verify email code.');
        console.log('[Instagram] Screenshot saved: /tmp/instagram-signup-status.png');

    } catch (err) {
        console.error('[Instagram] Error:', err.message);
        await page.screenshot({ path: '/tmp/instagram-error.png' });
    } finally {
        await page.close();
    }
}

async function createLinkedInCompanyPage(browser) {
    console.log('\n[LinkedIn] Starting company page creation...');
    const page = await browser.newPage();

    try {
        // LinkedIn company pages require a personal account first
        // But we can create the company page structure
        await page.goto('https://www.linkedin.com/company/new/', { waitUntil: 'networkidle2', timeout: 30000 });
        console.log('[LinkedIn] Loaded company creation page');

        // Fill company details
        await page.waitForSelector('input[name="name"]', { timeout: 10000 });
        await page.type('input[name="name"]', 'Fankaar Digital', { delay: 50 });

        // Company URL
        await page.type('input[name="url"]', 'fankaar.digital', { delay: 50 });

        // Industry
        await page.click('input[name="industry"]');
        await page.waitForTimeout(500);
        await page.type('input[name="industry"]', 'Marketing');
        await page.waitForTimeout(500);
        await page.keyboard.press('Enter');

        // Company size
        await page.select('select[name="size"]', '11-50');

        // Type
        await page.select('select[name="type"]', 'PRIV');

        // Submit
        await page.click('button[type="submit"]');
        console.log('[LinkedIn] Submitted company page form');

        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/tmp/linkedin-company-status.png' });

        console.log('[LinkedIn] Company page creation initiated.');
        console.log('[LinkedIn] Screenshot saved: /tmp/linkedin-company-status.png');

    } catch (err) {
        console.error('[LinkedIn] Error:', err.message);
        await page.screenshot({ path: '/tmp/linkedin-error.png' });
    } finally {
        await page.close();
    }
}

async function setupTwitterAccount(browser) {
    console.log('\n[Twitter/X] Starting account setup...');
    const page = await browser.newPage();

    try {
        await page.goto('https://twitter.com/i/flow/signup', { waitUntil: 'networkidle2', timeout: 30000 });
        console.log('[Twitter] Loaded signup flow');

        // Twitter has a multi-step signup flow
        await page.waitForTimeout(2000);

        // Step 1: Name
        await page.type('input[name="name"]', 'Fankaar Digital', { delay: 50 });

        // Use email
        await page.click('input[name="email"]');
        await page.waitForTimeout(500);
        await page.type('input[name="email"]', 'fankaar.social@gmail.com', { delay: 50 });

        // Next
        await page.click('div[role="button"]:has-text("Next")');

        console.log('[Twitter] Initial form submitted. Check email for verification.');
        await page.screenshot({ path: '/tmp/twitter-signup-status.png' });

    } catch (err) {
        console.error('[Twitter] Error:', err.message);
        await page.screenshot({ path: '/tmp/twitter-error.png' });
    } finally {
        await page.close();
    }
}

function generateSecurePassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 16; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
}

async function saveCredentials(credentials) {
    const credsPath = path.join(__dirname, 'social-credentials.json');
    fs.writeFileSync(credsPath, JSON.stringify(credentials, null, 2));
    console.log(`[Account Creator] Credentials saved to ${credsPath}`);
}

async function main() {
    console.log('═══════════════════════════════════════════════════════');
    console.log('  FANKAAR DIGITAL — Social Account Creator');
    console.log('  Using Chrome DevTools Protocol (CDP)');
    console.log('═══════════════════════════════════════════════════════\n');

    // Check if Chrome is running with CDP
    try {
        const response = await fetch(`${CDP_URL}/json/version`);
        if (!response.ok) throw new Error('CDP not available');
        console.log('[Account Creator] Chrome CDP is active\n');
    } catch {
        console.error('[Account Creator] Chrome CDP not found!');
        console.log('[Account Creator] Start Chrome with:');
        console.log('  Google Chrome --remote-debugging-port=18690');
        process.exit(1);
    }

    const browser = await connectToChrome();

    const credentials = {
        agency: AGENCY_NAME,
        createdAt: new Date().toISOString(),
        accounts: {}
    };

    try {
        // Create accounts in priority order
        console.log('\n--- PRIORITY 1: LinkedIn (B2B leads) ---');
        // LinkedIn requires personal account for company page
        // We'll note this and create company page separately
        console.log('[LinkedIn] Note: Requires personal LinkedIn account first');
        console.log('[LinkedIn] Company page structure prepared in script');

        console.log('\n--- PRIORITY 2: Instagram (Brand visibility) ---');
        await createInstagramAccount(browser);
        credentials.accounts.instagram = {
            username: 'fankaar.digital',
            email: 'fankaar.social@gmail.com',
            status: 'pending_verification'
        };

        console.log('\n--- PRIORITY 3: Twitter/X (Thought leadership) ---');
        await setupTwitterAccount(browser);
        credentials.accounts.twitter = {
            username: 'fankaardigital',
            email: 'fankaar.social@gmail.com',
            status: 'pending_verification'
        };

        console.log('\n--- PRIORITY 4: TikTok (Viral potential) ---');
        console.log('[TikTok] Requires phone verification. Use SMS service or manual creation.');
        credentials.accounts.tiktok = {
            username: 'fankaar.digital',
            status: 'manual_creation_needed'
        };

        // Save credentials
        await saveCredentials(credentials);

        console.log('\n═══════════════════════════════════════════════════════');
        console.log('  ACCOUNT CREATION SUMMARY');
        console.log('═══════════════════════════════════════════════════════');
        console.log('Instagram:  Initiated (verify email to complete)');
        console.log('LinkedIn:   Company page structure ready (needs personal account)');
        console.log('Twitter/X:  Initiated (verify email to complete)');
        console.log('TikTok:     Manual creation recommended (phone verification)');
        console.log('\nNext steps:');
        console.log('1. Check fankaar.social@gmail.com for verification emails');
        console.log('2. Complete verification on each platform');
        console.log('3. Upload profile picture and bio');
        console.log('4. Connect accounts to Missandei (social agent)');
        console.log('═══════════════════════════════════════════════════════');

    } catch (err) {
        console.error('[Account Creator] Fatal error:', err);
    } finally {
        await browser.disconnect();
        console.log('\n[Account Creator] Disconnected from Chrome');
    }
}

main().catch(console.error);
