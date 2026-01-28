<template>
  <div class="knowledge-page">
    <Toolbar :username="username" />
    <div class="main-content">
      <div class="page-header">
        <h2>知识库管理</h2>
        <div class="header-actions">
          <button class="upload-btn" @click="showUploadModal = true">
            <i class="upload-icon"></i> 上传文档
          </button>
          <button class="refresh-btn" @click="fetchDocuments">
            <i class="refresh-icon"></i> 刷新
          </button>
        </div>
      </div>
      
      <!-- 文档列表 -->
      <div class="document-list">
        <div class="list-header">
          <div class="header-item">文件名</div>
          <div class="header-item status">状态</div>
          <div class="header-item type">类型</div>
          <div class="header-item date">上传时间</div>
          <div class="header-item actions">操作</div>
        </div>
        <div class="list-body">
          <div v-if="loading" class="loading-state">
            <span>加载中...</span>
          </div>
          <div v-else-if="documents.length === 0" class="empty-state">
            <span>暂无文档，点击"上传文档"添加</span>
          </div>
          <div v-else class="document-item" v-for="doc in documents" :key="doc.document_id">
            <div class="item-content">
              <div class="document-name">{{ doc.document_name }}</div>
              <div class="document-status" :class="doc.document_status">
                {{ getStatusText(doc.document_status) }}
              </div>
              <div class="document-type">{{ doc.document_type }}</div>
              <div class="document-date">{{ formatDate(doc.created_at) }}</div>
              <div class="document-actions">
                <button class="action-btn view-btn" @click="viewDocument(doc.document_id)">
                  查看
                </button>
                <button class="action-btn chunks-btn" @click="viewChunks(doc.document_id)">
                  查看切片
                </button>
                <button class="action-btn delete-btn" @click="deleteDocument(doc.document_id)">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination">
        <button class="page-btn" @click="changePage(currentPage - 1)" :disabled="currentPage === 1">
          上一页
        </button>
        <span class="page-info">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button class="page-btn" @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">
          下一页
        </button>
      </div>
      
      <!-- 上传文档模态框 -->
      <div v-if="showUploadModal" class="modal-overlay" @click="showUploadModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>上传文档</h3>
            <button class="close-btn" @click="showUploadModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="upload-area" :class="{ dragging: isDragging }" @dragover.prevent @dragenter.prevent @dragleave.prevent @drop="handleDrop" @click="triggerFileInput">
              <input type="file" ref="fileInput" class="file-input" @change="handleFileSelect" accept=".pdf,.doc,.docx,.txt">
              <div class="upload-hint">
                <i class="upload-hint-icon">📁</i>
                <p>点击或拖拽文件到此处上传</p>
                <p class="supported-types">支持的文件类型：PDF, Word, TXT</p>
              </div>
              <div v-if="selectedFile" class="selected-file">
                <span class="file-name">{{ selectedFile.name }}</span>
                <button class="remove-file" @click="selectedFile = null">移除</button>
              </div>
            </div>
            <div class="upload-progress" v-if="uploadProgress > 0">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <span class="progress-text">{{ uploadProgress }}%</span>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="showUploadModal = false">取消</button>
            <button class="confirm-btn" @click="uploadFile" :disabled="!selectedFile || uploading">
              {{ uploading ? '上传中...' : '确认上传' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- 查看文档模态框 -->
      <div v-if="selectedDocument" class="modal-overlay" @click="selectedDocument = null">
        <div class="modal-content document-view-modal" @click.stop>
          <div class="modal-header">
            <h3>{{ selectedDocument.document_name }}</h3>
            <button class="close-btn" @click="selectedDocument = null">×</button>
          </div>
          <div class="modal-body">
            <div class="document-details">
              <div class="detail-item">
                <label>文档ID:</label>
                <span>{{ selectedDocument.document_id }}</span>
              </div>
              <div class="detail-item">
                <label>文件名:</label>
                <span>{{ selectedDocument.document_name }}</span>
              </div>
              <div class="detail-item">
                <label>类型:</label>
                <span>{{ selectedDocument.document_type }}</span>
              </div>
              <div class="detail-item">
                <label>状态:</label>
                <span class="status-badge" :class="selectedDocument.document_status">
                  {{ getStatusText(selectedDocument.document_status) }}
                </span>
              </div>
              <div class="detail-item">
                <label>上传时间:</label>
                <span>{{ formatDate(selectedDocument.created_at) }}</span>
              </div>
              <div class="detail-item">
                <label>更新时间:</label>
                <span>{{ formatDate(selectedDocument.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 查看切片模态框 -->
      <div v-if="showChunksModal" class="modal-overlay" @click="showChunksModal = false">
        <div class="modal-content chunks-modal" @click.stop>
          <div class="modal-header">
            <h3>文档切片 - {{ currentChunksDocumentName }}</h3>
            <button class="close-btn" @click="showChunksModal = false">×</button>
          </div>
          <div class="modal-body">
            <div v-if="loadingChunks" class="loading-state">
              <span>加载切片中...</span>
            </div>
            <div v-else-if="documentChunks.length === 0" class="empty-state">
              <span>暂无切片</span>
            </div>
            <div v-else class="chunks-list">
              <div class="chunk-item" v-for="chunk in documentChunks" :key="chunk.chunk_id">
                <div class="chunk-header">
                  <span class="chunk-index">切片 {{ chunk.index + 1 }}</span>
                  <span class="chunk-date">{{ formatDate(chunk.created_at) }}</span>
                </div>
                <div class="chunk-content">{{ chunk.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Toolbar from './Toolbar.vue';
// 导入文档相关API
import { documentAPI } from '../api/chat';

export default {
  name: 'KnowledgePage',
  components: {
    Toolbar
  },
  data() {
    return {
      username: '用户',
      documents: [],
      loading: false,
      uploading: false,
      uploadProgress: 0,
      showUploadModal: false,
      isDragging: false,
      selectedFile: null,
      selectedDocument: null,
      showChunksModal: false,
      currentChunksDocumentName: '',
      documentChunks: [],
      loadingChunks: false,
      currentPage: 1,
      pageSize: 10,
      total: 0
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize);
    }
  },
  mounted() {
    this.username = localStorage.getItem('username') || '用户';
    this.fetchDocuments();
  },
  methods: {
    async fetchDocuments() {
      this.loading = true;
      try {
        // 调用API获取文档列表
        const response = await documentAPI.getDocuments(
          this.currentPage,
          this.pageSize
        );
        
        // 使用实际API返回的数据
        this.documents = response.documents || [];
        this.total = response.total || 0;
      } catch (error) {
        console.error('获取文档失败:', error);
        alert('获取文档失败，请重试');
      } finally {
        this.loading = false;
      }
    },
    
    async uploadFile() {
      if (!this.selectedFile) return;
      
      this.uploading = true;
      this.uploadProgress = 0;
      
      try {
        // 调用API上传文件
        await documentAPI.uploadDocument(
          this.selectedFile,
          null // task_id 可选
        );
        
        // 上传完成
        this.uploadProgress = 100;
        this.uploading = false;
        this.showUploadModal = false;
        this.selectedFile = null;
        await this.fetchDocuments();
        alert('文件上传成功');
      } catch (error) {
        console.error('上传文件失败:', error);
        alert('上传文件失败，请重试');
        this.uploading = false;
      }
    },
    
    handleFileSelect(event) {
      if (event.target.files.length > 0) {
        this.selectedFile = event.target.files[0];
      }
    },
    
    handleDrop(event) {
      event.preventDefault();
      this.isDragging = false;
      if (event.dataTransfer.files.length > 0) {
        this.selectedFile = event.dataTransfer.files[0];
      }
    },
    
    triggerFileInput() {
      // 触发文件输入框的点击事件，调起本地文件选择窗口
      this.$refs.fileInput.click();
    },
    
    viewDocument(documentId) {
      const doc = this.documents.find(d => d.document_id === documentId);
      if (doc) {
        this.selectedDocument = doc;
      }
    },
    
    async viewChunks(documentId) {
      const doc = this.documents.find(d => d.document_id === documentId);
      if (doc) {
        this.currentChunksDocumentName = doc.document_name;
        this.loadingChunks = true;
        this.showChunksModal = true;
        
        try {
          // 调用API获取文档切片
          const response = await documentAPI.getDocumentChunks(documentId);
          // 转换为组件需要的格式
          this.documentChunks = response.chunks.map((chunk, index) => ({
            chunk_id: chunk.chunk_id,
            content: chunk.content,
            index: index,
            created_at: chunk.created_at
          }));
        } catch (error) {
          console.error('获取文档切片失败:', error);
          alert('获取文档切片失败，请重试');
        } finally {
          this.loadingChunks = false;
        }
      }
    },
    
    async deleteDocument(documentId) {
      if (confirm('确定要删除该文档吗？')) {
        try {
          // 调用API删除文档
          await documentAPI.deleteDocument(documentId);
          
          // 删除成功后刷新文档列表
          await this.fetchDocuments();
          alert('文档删除成功');
        } catch (error) {
          console.error('删除文档失败:', error);
          alert('删除文档失败，请重试');
        }
      }
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
        this.fetchDocuments();
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'pending': '处理中',
        'completed': '已完成',
        'failed': '失败',
        'deleted': '已删除'
      };
      return statusMap[status] || status;
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString();
    }
  }
}
</script>

<style scoped>
.knowledge-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.main-content {
  margin-top: 60px;
  padding: 20px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eaeaea;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.upload-btn, .refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn {
  background-color: #1890ff;
  color: white;
}

.upload-btn:hover {
  background-color: #40a9ff;
}

.refresh-btn {
  background-color: #f0f0f0;
  color: #333;
}

.refresh-btn:hover {
  background-color: #e0e0e0;
}

.upload-icon::before {
  content: "📤";
  font-size: 16px;
}

.refresh-icon::before {
  content: "🔄";
  font-size: 16px;
}

.document-list {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.list-header {
  display: flex;
  background-color: #fafafa;
  padding: 12px 20px;
  border-bottom: 1px solid #eaeaea;
  font-weight: 600;
  font-size: 14px;
  color: #666;
}

.header-item {
  flex: 1;
}

.header-item.status {
  flex: 0.5;
}

.header-item.type {
  flex: 0.3;
}

.header-item.date {
  flex: 1;
}

.header-item.actions {
  flex: 0.5;
  text-align: center;
}

.list-body {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.loading-state, .empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
}

.document-item {
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.document-item:hover {
  background-color: #fafafa;
}

.item-content {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  font-size: 14px;
}

.document-name {
  flex: 1;
  font-weight: 500;
  color: #333;
}

.document-status {
  flex: 0.5;
  text-align: center;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.document-status.pending {
  background-color: #fff7e6;
  color: #fa8c16;
}

.document-status.completed {
  background-color: #f6ffed;
  color: #52c41a;
}

.document-status.failed {
  background-color: #fff2f0;
  color: #ff4d4f;
}

.document-type {
  flex: 0.3;
  text-align: center;
  color: #666;
}

.document-date {
  flex: 1;
  color: #999;
  font-size: 13px;
}

.document-actions {
  flex: 0.5;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-btn {
  padding: 4px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background-color: white;
  color: #333;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.action-btn.view-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.action-btn.chunks-btn:hover {
  border-color: #52c41a;
  color: #52c41a;
}

.action-btn.delete-btn:hover {
  border-color: #ff4d4f;
  color: #ff4d4f;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  gap: 15px;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background-color: white;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.document-view-modal, .chunks-modal {
  max-width: 800px;
}

.chunks-modal {
  max-height: 90vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eaeaea;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background-color: #f0f0f0;
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #eaeaea;
}

.cancel-btn, .confirm-btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background-color: white;
  color: #333;
}

.cancel-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.confirm-btn {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}

.confirm-btn:hover:not(:disabled) {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 上传区域样式 */
.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.upload-area:hover, .upload-area.dragging {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.file-input {
  display: none;
}

.upload-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.upload-hint-icon {
  font-size: 48px;
}

.upload-hint p {
  margin: 0;
  color: #666;
}

.supported-types {
  font-size: 12px;
  color: #999;
}

.selected-file {
  margin-top: 20px;
  padding: 10px 15px;
  background-color: #f0f0f0;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 10px;
}

.remove-file {
  background: none;
  border: none;
  color: #ff4d4f;
  font-size: 14px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.remove-file:hover {
  background-color: #fff2f0;
}

.upload-progress {
  margin-top: 20px;
}

.progress-bar {
  height: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background-color: #1890ff;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  font-size: 14px;
  color: #666;
  text-align: center;
}

/* 文档详情样式 */
.document-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-item {
  display: flex;
  gap: 15px;
}

.detail-item label {
  width: 100px;
  font-weight: 500;
  color: #666;
  text-align: right;
}

.detail-item span {
  flex: 1;
  color: #333;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background-color: #fff7e6;
  color: #fa8c16;
}

.status-badge.completed {
  background-color: #f6ffed;
  color: #52c41a;
}

.status-badge.failed {
  background-color: #fff2f0;
  color: #ff4d4f;
}

/* 切片列表样式 */
.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chunk-item {
  padding: 15px;
  border: 1px solid #eaeaea;
  border-radius: 6px;
  background-color: #fafafa;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaeaea;
}

.chunk-index {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.chunk-date {
  font-size: 12px;
  color: #999;
}

.chunk-content {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
}
</style>