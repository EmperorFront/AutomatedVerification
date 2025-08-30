// verifyKey-native.js
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

async function fetchRemoteJS(url) {
  return new Promise((resolve, reject) => {
    // 自动选择协议模块
    const lib = url.startsWith('https') ? require('https') : require('http');
    
    lib.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

// =============== 解密逻辑（改造后） =================

/**
 * 模拟 CryptoJS.AES.decrypt 的解密方法
 * @param {string} encryptedBase64 - CryptoJS 输出的 Base64 密文
 * @param {string} passphrase - 加密/解密用的密码
 */
function decryptAES(encryptedBase64, passphrase) {
  const encrypted = Buffer.from(encryptedBase64, 'base64');

  // CryptoJS/OpenSSL 格式: 前 8 字节是 "Salted__", 后面 8 字节是 salt
  const magic = encrypted.slice(0, 8).toString();
  if (magic !== 'Salted__') {
    throw new Error('Invalid OpenSSL salt header.');
  }
  const salt = encrypted.slice(8, 16);
  const ciphertext = encrypted.slice(16);

  // 用 EVP_BytesToKey 派生 key 和 iv
  const keyIv = EVP_BytesToKey(passphrase, salt, 32, 16); // AES-256-CBC
  const key = keyIv.key;
  const iv = keyIv.iv;

  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
  let decrypted = decipher.update(ciphertext);
  decrypted = Buffer.concat([decrypted, decipher.final()]);

  return decrypted.toString('utf8');
}

/**
 * 实现 OpenSSL 的 EVP_BytesToKey
 * @param {string} passphrase - 密码
 * @param {Buffer} salt - 8 字节 salt
 * @param {number} keyLen - 需要的 key 长度
 * @param {number} ivLen - 需要的 iv 长度
 */
function EVP_BytesToKey(passphrase, salt, keyLen, ivLen) {
  let data = Buffer.alloc(0);
  let m = Buffer.alloc(0);
  while (data.length < keyLen + ivLen) {
    const md5 = crypto.createHash('md5');
    md5.update(Buffer.concat([m, Buffer.from(passphrase), salt]));
    m = md5.digest();
    data = Buffer.concat([data, m]);
  }
  return {
    key: data.slice(0, keyLen),
    iv: data.slice(keyLen, keyLen + ivLen),
  };
}

// =============== 主逻辑部分（保持不变） =================

async function verifyPhoneDataKey() {
  const phonedataPath = path.join(__dirname, 'phonedata.js');

  // 读取 phonedata 并生成 MD5
  const phoneContent = fs.readFileSync(phonedataPath, 'utf-8');
  const md5 = crypto.createHash('md5').update(phoneContent, 'utf-8').digest('hex');
  console.log(`phonedata.md5: ${md5}`);

  // 请求远程 JS
  const url = 'http://101.43.152.10:8080/api/jsonp';
  let remoteContent;
  try {
    remoteContent = await fetchRemoteJS(url);
    console.log(`远程 JS 内容长度: ${remoteContent.length}`);
    console.log(`远程 JS 内容: ${remoteContent.slice(0, 100)}...`); // 只打印前100字符

  } catch (err) {
    console.error('请求远程 JS 失败:', err);
    return;
  }

  // 按 ; 分割
  const items = remoteContent.split(';').map(i => i.trim()).filter(i => i.length > 0);
  console.log(`远程 JS 共 ${items.length} 个元素`);
  console.log(`第一个 ${items[0]} 为`);

  // 遍历解密
  const key = 'c';
  for (const encrypted of items) {
    try {
      const decrypted = decryptAES(encrypted, key);
      console.log('所有密钥解密后' + decrypted);
      console.log('所有密钥解密后' + md5);

      if (decrypted && decrypted.includes(md5)) {
        console.log('找到匹配元素，解密内容:');
        console.log(decrypted);
        return decrypted;
      }
    } catch (err) {
      console.warn('解密失败，可能不是有效的 AES Base64:', encrypted);
    }
  }

  console.log('未找到匹配密钥');
  return null;
}

// 如果直接运行
if (require.main === module) {
  verifyPhoneDataKey().catch(console.error);
}

module.exports = { verifyPhoneDataKey };
