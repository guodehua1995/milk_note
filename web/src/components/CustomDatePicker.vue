<template>
  <div class="custom-date-picker">
    <label v-if="label">{{ label }}</label>
    <div class="input-group">
      <input 
        v-model="localValue" 
        type="date" 
        :class="['form-input', className]"
        :required="required"
        @input="handleInput"
      />
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'CustomDatePicker',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      default: ''
    },
    className: {
      type: String,
      default: ''
    },
    required: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const localValue = ref('')

    // 监听props变化
    watch(() => props.modelValue, (newValue) => {
      if (newValue) {
        // 转换ISO格式到date格式
        const date = new Date(newValue)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        localValue.value = `${year}-${month}-${day}`
      } else {
        localValue.value = ''
      }
    }, { immediate: true })

    // 处理输入变化
    const handleInput = (event) => {
      const value = event.target.value
      if (value) {
        // 转换为ISO格式
        const isoValue = new Date(value).toISOString()
        emit('update:modelValue', isoValue)
      } else {
        emit('update:modelValue', null)
      }
    }

    return {
      localValue,
      handleInput
    }
  }
}
</script>

<style scoped>
.custom-date-picker {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.custom-date-picker label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.input-group {
  position: relative;
}

.form-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  width: 100%;
}

.form-input:hover {
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

.form-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}
</style>