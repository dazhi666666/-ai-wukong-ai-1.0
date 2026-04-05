import { test, expect } from '@playwright/test';

test.describe('Stock Analysis Feature', () => {
  test('should display analysis settings component', async ({ page }) => {
    await page.goto('/');
    
    // Click on the stock analysis menu item in the sidebar
    const stockAnalysisMenuItem = page.locator('.nav-item').filter({ hasText: '股票分析' });
    await stockAnalysisMenuItem.click();
    
    // Wait for navigation to complete
    await page.waitForTimeout(1000);
    
    // Check if the analysis settings component is present
    const analysisSettings = page.locator('.analysis-settings');
    await expect(analysisSettings).toBeVisible();
  });

  test('should allow selecting prompt version', async ({ page }) => {
    await page.goto('/');
    
    // Click on the stock analysis menu item in the sidebar
    const stockAnalysisMenuItem = page.locator('.nav-item').filter({ hasText: '股票分析' });
    await stockAnalysisMenuItem.click();
    
    // Wait for navigation to complete
    await page.waitForTimeout(1000);
    
    // Select prompt version
    const promptSelect = page.locator('.prompt-version-select');
    await expect(promptSelect).toBeVisible();
    
    await promptSelect.selectOption('conservative');
    const selectedValue = await promptSelect.inputValue();
    expect(selectedValue).toBe('conservative');
    
    await promptSelect.selectOption('neutral');
    const selectedValue2 = await promptSelect.inputValue();
    expect(selectedValue2).toBe('neutral');
    
    await promptSelect.selectOption('aggressive');
    const selectedValue3 = await promptSelect.inputValue();
    expect(selectedValue3).toBe('aggressive');
  });

  test('should display agent cards with correct information', async ({ page }) => {
    await page.goto('/');
    
    // Click on the stock analysis menu item in the sidebar
    const stockAnalysisMenuItem = page.locator('.nav-item').filter({ hasText: '股票分析' });
    await stockAnalysisMenuItem.click();
    
    // Wait for navigation to complete
    await page.waitForTimeout(1000);
    
    // Check for agent cards
    const agentCards = page.locator('.agent-card');
    await expect(agentCards).toHaveCount(4); // We have 4 core agents
    
    // Check first agent (fundamental analyst)
    const firstAgent = agentCards.first();
    await expect(firstAgent).toContainText('基本面分析师 v2.0');
    
    // Expand the agent card to see details
    const firstAgentHeader = firstAgent.locator('.agent-header');
    await firstAgentHeader.click();
    await page.waitForTimeout(500);
    
    await expect(firstAgent).toContainText('温度:0.2');
    await expect(firstAgent).toContainText('最大迭代:3');
    await expect(firstAgent).toContainText('超时时间:300s');
    
    // Check that it shows the correct tools
    await expect(firstAgent).toContainText('get_stock_fundamentals');
    await expect(firstAgent).toContainText('get_stock_financial');
  });

  test('should allow expanding/collapsing agent details', async ({ page }) => {
    await page.goto('/');
    
    // Click on the stock analysis menu item in the sidebar
    const stockAnalysisMenuItem = page.locator('.nav-item').filter({ hasText: '股票分析' });
    await stockAnalysisMenuItem.click();
    
    // Wait for navigation to complete
    await page.waitForTimeout(1000);
    
    // Click on first agent header to expand
    const firstAgentHeader = page.locator('.agent-card').first().locator('.agent-header');
    await firstAgentHeader.click();
    
    // Check if details are expanded
    const firstAgentDetails = page.locator('.agent-card').first().locator('.agent-details-content');
    await expect(firstAgentDetails).toBeVisible();
    
    // Click again to collapse
    await firstAgentHeader.click();
    
    // Check if details are collapsed
    await expect(firstAgentDetails).toBeHidden();
  });
});