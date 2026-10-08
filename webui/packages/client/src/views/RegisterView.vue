<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { markCookieSession } from "@/api/client";
import { registerAccount } from "@/api/auth";

const { t } = useI18n();
const router = useRouter();

const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const errorMsg = ref("");

async function handleRegister() {
  if (!username.value.trim() || !password.value || !confirmPassword.value) {
    errorMsg.value = t("register.credentialsRequired");
    return;
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = t("register.passwordMismatch");
    return;
  }

  loading.value = true;
  errorMsg.value = "";

  try {
    const session = await registerAccount(username.value.trim(), password.value);
    markCookieSession(session.user);
    router.replace("/hermes/chat");
  } catch (err: any) {
    errorMsg.value = err.message || t("register.failed");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="register-view">
    <div class="register-card">
      <div class="register-logo">
        <img src="/logo.png" alt="Deep Agent" width="80" height="80" />
      </div>
      <h1 class="register-title">{{ t("register.title") }}</h1>
      <p class="register-desc">{{ t("register.description") }}</p>
      <form class="register-form" @submit.prevent="handleRegister">
        <input
          v-model="username"
          type="text"
          class="register-input"
          :placeholder="t('login.usernamePlaceholder')"
          autofocus
        />
        <input
          v-model="password"
          type="password"
          class="register-input"
          :placeholder="t('login.passwordPlaceholder')"
        />
        <input
          v-model="confirmPassword"
          type="password"
          class="register-input"
          :placeholder="t('register.confirmPasswordPlaceholder')"
          @keyup.enter="handleRegister"
        />

        <div v-if="errorMsg" class="register-error">{{ errorMsg }}</div>
        <button type="submit" class="register-btn" :disabled="loading">
          {{ loading ? "..." : t("register.submit") }}
        </button>
      </form>
      <div class="register-footer">
        <RouterLink to="/" class="register-link">{{ t("register.backToLogin") }}</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use "@/styles/variables" as *;

.register-view {
  height: calc(100 * var(--vh));
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-primary;
}

.register-card {
  width: 480px;
  max-width: calc(100vw - 32px);
  padding: 56px;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  background: $bg-card;
  text-align: center;

  @media (max-width: $breakpoint-mobile) {
    padding: 32px 24px;
  }
}

.register-logo {
  margin-bottom: 24px;
}

.register-title {
  font-size: 26px;
  font-weight: 600;
  color: $text-primary;
  margin: 0 0 10px;
}

.register-desc {
  font-size: 14px;
  color: $text-muted;
  margin: 0 0 12px;
  line-height: 1.6;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.register-input {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid $border-color;
  border-radius: $radius-sm;
  font-size: 15px;
  color: $text-primary;
  background: $bg-input;
  outline: none;
  transition: border-color $transition-fast;
  box-sizing: border-box;
  font-family: $font-code;

  &::placeholder {
    color: $text-muted;
  }

  &:focus {
    border-color: $accent-primary;
  }
}

.register-error {
  font-size: 13px;
  color: $error;
  text-align: left;
}

.register-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: $radius-sm;
  background: $text-primary;
  color: var(--text-on-accent);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity $transition-fast;

  &:hover {
    opacity: 0.85;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.register-footer {
  margin-top: 18px;
  font-size: 13px;
}

.register-link {
  color: $accent-primary;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}
</style>
