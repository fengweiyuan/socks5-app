/**
 * 通用格式化工具函数
 * 统一处理各种数据格式化，避免显示 NaN undefined 等无效值
 */

/**
 * 格式化字节数
 * @param {number|string|null|undefined} bytes - 字节数
 * @returns {string} 格式化后的字节字符串
 */
export const formatBytes = (bytes) => {
  // 处理无效值
  if (bytes === null || bytes === undefined || isNaN(bytes) || bytes < 0) {
    return '0 B'
  }
  
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间
 * @param {string|Date|null|undefined} date - 日期
 * @returns {string} 格式化后的日期字符串
 */
export const formatDateTime = (date) => {
  if (!date) return '--'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return '--'
    return dateObj.toLocaleString()
  } catch (error) {
    return '--'
  }
}

/**
 * 格式化时间
 * @param {string|Date|null|undefined} date - 日期
 * @returns {string} 格式化后的时间字符串
 */
export const formatTime = (date) => {
  if (!date) return '--'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return '--'
    return dateObj.toLocaleTimeString()
  } catch (error) {
    return '--'
  }
}

/**
 * 格式化日期
 * @param {string|Date|null|undefined} date - 日期
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (date) => {
  if (!date) return '--'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return '--'
    return dateObj.toLocaleDateString()
  } catch (error) {
    return '--'
  }
}

/**
 * 格式化数字
 * @param {number|string|null|undefined} num - 数字
 * @param {number} decimals - 小数位数，默认2
 * @returns {string} 格式化后的数字字符串
 */
export const formatNumber = (num, decimals = 2) => {
  if (num === null || num === undefined || isNaN(num)) {
    return '0'
  }
  
  const number = parseFloat(num)
  if (isNaN(number)) return '0'
  
  return number.toFixed(decimals)
}

/**
 * 格式化百分比
 * @param {number|string|null|undefined} num - 数字
 * @param {number} decimals - 小数位数，默认2
 * @returns {string} 格式化后的百分比字符串
 */
export const formatPercent = (num, decimals = 2) => {
  if (num === null || num === undefined || isNaN(num)) {
    return '0%'
  }
  
  const number = parseFloat(num)
  if (isNaN(number)) return '0%'
  
  return (number * 100).toFixed(decimals) + '%'
}

/**
 * 格式化文件大小（人类可读）
 * @param {number|string|null|undefined} bytes - 字节数
 * @returns {string} 格式化后的文件大小字符串
 */
export const formatFileSize = (bytes) => {
  return formatBytes(bytes)
}

/**
 * 格式化网络速度
 * @param {number|string|null|undefined} bytesPerSecond - 每秒字节数
 * @returns {string} 格式化后的网络速度字符串
 */
export const formatNetworkSpeed = (bytesPerSecond) => {
  if (bytesPerSecond === null || bytesPerSecond === undefined || isNaN(bytesPerSecond) || bytesPerSecond < 0) {
    return '0 B/s'
  }
  
  if (bytesPerSecond === 0) return '0 B/s'
  
  const k = 1024
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k))
  return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化持续时间
 * @param {number|string|null|undefined} seconds - 秒数
 * @returns {string} 格式化后的持续时间字符串
 */
export const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined || isNaN(seconds) || seconds < 0) {
    return '0秒'
  }
  
  if (seconds === 0) return '0秒'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}
