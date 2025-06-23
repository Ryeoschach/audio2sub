/**
 * Audio2Sub API 前端测试脚本
 * 测试动态模型选择功能的 JavaScript 实现
 */

class Audio2SubAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * 获取可用模型列表
     */
    async getModels() {
        try {
            const response = await fetch(`${this.baseUrl}/models/`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('获取模型列表失败:', error);
            throw error;
        }
    }

    /**
     * 上传文件进行转录
     * @param {File} file - 音频文件
     * @param {Object} options - 转录选项
     */
    async uploadFile(file, options = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('model', options.model || 'base');
            formData.append('language', options.language || 'auto');
            formData.append('output_format', options.output_format || 'both');
            formData.append('task', options.task || 'transcribe');

            const response = await fetch(`${this.baseUrl}/upload/`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('文件上传失败:', error);
            throw error;
        }
    }

    /**
     * 检查任务状态
     * @param {string} taskId - 任务ID
     */
    async checkStatus(taskId) {
        try {
            const response = await fetch(`${this.baseUrl}/status/${taskId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('状态检查失败:', error);
            throw error;
        }
    }

    /**
     * 等待任务完成
     * @param {string} taskId - 任务ID
     * @param {number} maxWait - 最大等待时间(毫秒)
     * @param {Function} onProgress - 进度回调函数
     */
    async waitForCompletion(taskId, maxWait = 300000, onProgress = null) {
        const startTime = Date.now();
        const checkInterval = 3000; // 3秒检查一次
        
        while (Date.now() - startTime < maxWait) {
            try {
                const status = await this.checkStatus(taskId);
                
                if (onProgress) {
                    onProgress(status);
                }
                
                console.log(`任务 ${taskId} 状态:`, status.state);
                
                if (status.state === 'SUCCESS') {
                    console.log('✅ 任务完成成功!');
                    return status.result;
                } else if (status.state === 'FAILURE') {
                    console.error('❌ 任务失败:', status);
                    throw new Error(`任务失败: ${status.result?.status || '未知错误'}`);
                } else if (status.state === 'PROGRESS') {
                    const progressInfo = status.result?.status || '处理中...';
                    console.log(`🔄 进度: ${progressInfo}`);
                }
                
                // 等待下次检查
                await new Promise(resolve => setTimeout(resolve, checkInterval));
                
            } catch (error) {
                console.error('状态检查出错:', error);
                await new Promise(resolve => setTimeout(resolve, checkInterval));
            }
        }
        
        throw new Error('等待任务完成超时');
    }

    /**
     * 健康检查
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return response.ok;
        } catch (error) {
            console.error('健康检查失败:', error);
            return false;
        }
    }
}

/**
 * API 测试类
 */
class APITester {
    constructor(api) {
        this.api = api;
    }

    /**
     * 创建测试文件
     */
    createTestFile() {
        const testContent = `
Hello, this is a test audio file for Audio2Sub API testing.
We are testing different Whisper models including tiny, base, and small.
Each model has different speed and accuracy characteristics.
This test helps validate the dynamic model selection functionality.
Testing Chinese content: 你好，这是一个测试文件。
Testing numbers: 1, 2, 3, 4, 5.
Testing punctuation: Hello! How are you? I'm fine, thank you.
        `.trim();
        
        const blob = new Blob([testContent], { type: 'text/plain' });
        return new File([blob], 'test_audio.txt', { type: 'text/plain' });
    }

    /**
     * 测试单个模型
     */
    async testModel(file, config) {
        console.log(`\n🧪 测试模型: ${config.model}`);
        console.log(`描述: ${config.description}`);
        console.log(`参数: 语言=${config.language}, 格式=${config.output_format}`);
        
        try {
            // 1. 上传文件
            const uploadResult = await this.api.uploadFile(file, {
                model: config.model,
                language: config.language,
                output_format: config.output_format,
                task: config.task || 'transcribe'
            });
            
            console.log('✅ 上传成功:', uploadResult);
            
            // 2. 等待完成，并显示进度
            const result = await this.api.waitForCompletion(
                uploadResult.task_id,
                300000, // 5分钟超时
                (status) => {
                    if (status.state === 'PROGRESS' && status.result?.status) {
                        console.log(`📊 ${config.model}: ${status.result.status}`);
                    }
                }
            );
            
            console.log(`✅ ${config.model} 模型测试完成:`, result);
            
            // 3. 返回测试结果
            return {
                model: config.model,
                config: config,
                success: true,
                result: result,
                uploadResult: uploadResult
            };
            
        } catch (error) {
            console.error(`❌ ${config.model} 模型测试失败:`, error);
            return {
                model: config.model,
                config: config,
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 运行完整的模型比较测试
     */
    async runModelComparisonTest() {
        console.log('🚀 开始 Audio2Sub API 模型比较测试');
        console.log('=' .repeat(50));
        
        try {
            // 1. 健康检查
            console.log('🔍 健康检查...');
            const isHealthy = await this.api.healthCheck();
            if (!isHealthy) {
                throw new Error('API 健康检查失败，请确保服务器正在运行');
            }
            console.log('✅ API 健康检查通过');
            
            // 2. 获取可用模型
            console.log('\n📋 获取可用模型...');
            const modelsData = await this.api.getModels();
            console.log('✅ 可用模型:', modelsData);
            
            // 3. 创建测试文件
            console.log('\n📁 创建测试文件...');
            const testFile = this.createTestFile();
            console.log(`✅ 测试文件已创建: ${testFile.name} (${testFile.size} bytes)`);
            
            // 4. 定义测试配置
            const testConfigs = [
                {
                    model: 'tiny',
                    description: '最快速度，适合实时处理',
                    language: 'auto',
                    output_format: 'srt'
                },
                {
                    model: 'base',
                    description: '平衡速度和质量，日常使用推荐',
                    language: 'zh',
                    output_format: 'vtt'
                },
                {
                    model: 'small',
                    description: '更高的准确度，专业转录',
                    language: 'auto',
                    output_format: 'both'
                }
            ];
            
            // 5. 运行测试
            console.log(`\n🔬 开始测试 ${testConfigs.length} 个模型配置...`);
            const results = [];
            
            for (let i = 0; i < testConfigs.length; i++) {
                const config = testConfigs[i];
                console.log(`\n--- 测试 ${i + 1}/${testConfigs.length} ---`);
                
                const testResult = await this.testModel(testFile, config);
                results.push(testResult);
                
                console.log('-'.repeat(40));
            }
            
            // 6. 显示测试总结
            this.printTestSummary(results);
            
            return results;
            
        } catch (error) {
            console.error('❌ 测试过程中出错:', error);
            throw error;
        }
    }

    /**
     * 打印测试总结
     */
    printTestSummary(results) {
        console.log('\n' + '='.repeat(60));
        console.log('📊 模型比较测试总结');
        console.log('='.repeat(60));
        
        if (results.length === 0) {
            console.log('❌ 没有测试结果');
            return;
        }
        
        const successCount = results.filter(r => r.success).length;
        const totalCount = results.length;
        
        console.log(`\n📈 总体统计:`);
        console.log(`   总测试数: ${totalCount}`);
        console.log(`   成功: ${successCount}`);
        console.log(`   失败: ${totalCount - successCount}`);
        console.log(`   成功率: ${(successCount / totalCount * 100).toFixed(1)}%`);
        
        for (const result of results) {
            console.log(`\n🔹 模型: ${result.model.toUpperCase()}`);
            
            if (result.success) {
                console.log(`   ✅ 状态: 成功`);
                
                if (result.result?.timing) {
                    const timing = result.result.timing;
                    console.log(`   ⏱️  处理时间: ${timing.total_time || 'N/A'}s`);
                    console.log(`   🎙️  转录时间: ${timing.transcription_time || 'N/A'}s`);
                }
                
                if (result.result?.transcription_params) {
                    const params = result.result.transcription_params;
                    console.log(`   📝 参数:`);
                    console.log(`     - 语言: ${params.language || 'N/A'}`);
                    console.log(`     - 输出格式: ${params.output_format || 'N/A'}`);
                    console.log(`     - 任务类型: ${params.task_type || 'N/A'}`);
                }
                
                if (result.result?.files) {
                    const files = result.result.files;
                    console.log(`   📄 生成文件: ${files.length} 个`);
                    files.forEach(file => {
                        console.log(`     - ${file.filename} (${file.type})`);
                    });
                }
                
                if (result.result?.full_text) {
                    const text = result.result.full_text;
                    const preview = text.length > 80 ? text.substring(0, 80) + '...' : text;
                    console.log(`   💬 转录预览: ${preview}`);
                }
                
            } else {
                console.log(`   ❌ 状态: 失败`);
                console.log(`   🚨 错误: ${result.error || '未知错误'}`);
            }
        }
        
        if (successCount === totalCount) {
            console.log('\n🎉 所有测试都成功完成！');
        } else {
            console.log(`\n⚠️  ${totalCount - successCount} 个测试失败`);
        }
    }
}

/**
 * 运行测试的主函数
 */
async function runTests() {
    try {
        // 创建 API 实例
        const api = new Audio2SubAPI();
        
        // 创建测试器
        const tester = new APITester(api);
        
        // 运行测试
        const results = await tester.runModelComparisonTest();
        
        console.log('\n✅ 所有测试完成!');
        return results;
        
    } catch (error) {
        console.error('🚨 测试失败:', error);
        throw error;
    }
}

// 如果在浏览器环境中，可以直接运行
if (typeof window !== 'undefined') {
    // 浏览器环境
    window.Audio2SubAPI = Audio2SubAPI;
    window.APITester = APITester;
    window.runTests = runTests;
    
    console.log('🌐 Audio2Sub API 测试脚本已加载');
    console.log('💡 使用方法:');
    console.log('   runTests() - 运行完整测试');
    console.log('   new Audio2SubAPI() - 创建 API 实例');
} else if (typeof module !== 'undefined') {
    // Node.js 环境
    module.exports = {
        Audio2SubAPI,
        APITester,
        runTests
    };
}

/*
使用示例:

// 1. 在浏览器控制台中运行完整测试
runTests();

// 2. 单独使用 API
const api = new Audio2SubAPI();
api.getModels().then(models => console.log(models));

// 3. 上传文件
const file = document.getElementById('fileInput').files[0];
api.uploadFile(file, { model: 'base', language: 'zh' })
   .then(result => console.log(result));

// 4. 监控任务
api.waitForCompletion('task-id-here')
   .then(result => console.log('完成:', result))
   .catch(error => console.error('失败:', error));
*/
