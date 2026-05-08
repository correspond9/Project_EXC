import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useAuthStore } from '../store/authStore';
import api from '../lib/api';

export default function ProfileScreen() {
  const { email, role, tradingMode, clearAuth } = useAuthStore();

  async function handleLogout() {
    try {
      await api.post('/api/auth/logout');
    } catch {}
    clearAuth();
  }

  function confirmLogout() {
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log Out', style: 'destructive', onPress: handleLogout },
    ]);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile</Text>

      <View style={styles.card}>
        <Row label="Email" value={email ?? ''} />
        <Row label="Role" value={role ?? ''} />
        <Row label="Trading Mode" value={tradingMode ?? ''} />
      </View>

      <TouchableOpacity
        style={styles.logoutBtn}
        onPress={confirmLogout}
        accessibilityLabel="Log out of your account"
        accessibilityRole="button"
      >
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </View>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117', padding: 16, paddingTop: 52 },
  title: { fontSize: 22, fontWeight: '700', color: '#e6edf3', marginBottom: 24 },
  card: {
    backgroundColor: '#161b22', borderRadius: 12, borderWidth: 1,
    borderColor: '#21262d', overflow: 'hidden',
  },
  row: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 14, borderBottomWidth: 1, borderBottomColor: '#21262d',
  },
  label: { fontSize: 14, color: '#8b949e' },
  value: { fontSize: 14, color: '#e6edf3', fontWeight: '600' },
  logoutBtn: {
    marginTop: 24, backgroundColor: 'rgba(239,68,68,0.1)', borderWidth: 1,
    borderColor: '#ef4444', borderRadius: 10, padding: 15, alignItems: 'center',
  },
  logoutText: { color: '#ef4444', fontWeight: '700', fontSize: 15 },
});
