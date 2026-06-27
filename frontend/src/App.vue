<script setup lang="ts">
</script>

<template>
  <router-view />
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #303133;
  background: url('/bg.png') no-repeat center center fixed;
  background-size: cover;
}
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.6);
  z-index: -1;
}
#app {
  min-height: 100vh;
  position: relative;
  z-index: 0;
}
</style>
