import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import api from '../lib/api';
import { useAuthStore } from '../store/authStore';

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();

  async function handleLogin() {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter email and password.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/api/auth/login', { email, password });
      const { user_id, role, trading_mode } = res.data;
      setAuth(user_id, email, role, trading_mode);
    } catch (err: any) {
      Alert.alert('Login Failed', err?.response?.data?.detail || 'Invalid credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Text style={styles.logo}>XChange</Text>
      <Text style={styles.subtitle}>Crypto Trading Platform</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        placeholderTextColor="#8b949e"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        accessibilityLabel="Email address"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor="#8b949e"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        accessibilityLabel="Password"
      />

      <TouchableOpacity
        style={styles.button}
        onPress={handleLogin}
        disabled={loading}
        accessibilityLabel="Sign in"
        accessibilityRole="button"
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Sign In</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => navigation.navigate('Register')}
        accessibilityLabel="Go to registration"
        accessibilityRole="button"
      >
        <Text style={styles.link}>Don't have an account? Register</Text>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117', justifyContent: 'center', padding: 24 },
  logo: { fontSize: 36, fontWeight: '700', color: '#3b82f6', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#8b949e', textAlign: 'center', marginBottom: 32 },
  input: {
    backgroundColor: '#161b22', borderWidth: 1, borderColor: '#21262d',
    borderRadius: 8, padding: 14, color: '#e6edf3', marginBottom: 12, fontSize: 15,
  },
  button: {
    backgroundColor: '#3b82f6', borderRadius: 8, padding: 15, alignItems: 'center', marginTop: 8,
  },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  link: { color: '#3b82f6', textAlign: 'center', marginTop: 20 },
});
