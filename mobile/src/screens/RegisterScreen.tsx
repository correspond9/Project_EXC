import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, KeyboardAvoidingView, Platform, Alert, ScrollView,
} from 'react-native';
import api from '../lib/api';

export default function RegisterScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'STUDENT' | 'TRADER'>('STUDENT');
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/api/auth/register', { email, password, role });
      Alert.alert('Success', 'Account created! Please sign in.', [
        { text: 'OK', onPress: () => navigation.navigate('Login') },
      ]);
    } catch (err: any) {
      Alert.alert('Registration Failed', err?.response?.data?.detail || 'Could not register.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }}>
        <Text style={styles.title}>Create Account</Text>

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

        <Text style={styles.label}>Account Type</Text>
        <View style={styles.roleRow}>
          {(['STUDENT', 'TRADER'] as const).map((r) => (
            <TouchableOpacity
              key={r}
              style={[styles.roleBtn, role === r && styles.roleBtnActive]}
              onPress={() => setRole(r)}
              accessibilityLabel={`Select ${r} role`}
              accessibilityRole="radio"
              accessibilityState={{ checked: role === r }}
            >
              <Text style={[styles.roleBtnText, role === r && styles.roleBtnTextActive]}>{r}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={styles.button}
          onPress={handleRegister}
          disabled={loading}
          accessibilityLabel="Create account"
          accessibilityRole="button"
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Register</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
          <Text style={styles.link}>Already have an account? Sign In</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117', padding: 24 },
  title: { fontSize: 28, fontWeight: '700', color: '#e6edf3', marginBottom: 24, textAlign: 'center' },
  input: {
    backgroundColor: '#161b22', borderWidth: 1, borderColor: '#21262d',
    borderRadius: 8, padding: 14, color: '#e6edf3', marginBottom: 12, fontSize: 15,
  },
  label: { color: '#8b949e', marginBottom: 8, fontSize: 13 },
  roleRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  roleBtn: {
    flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#21262d',
    alignItems: 'center',
  },
  roleBtnActive: { borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)' },
  roleBtnText: { color: '#8b949e', fontWeight: '600' },
  roleBtnTextActive: { color: '#3b82f6' },
  button: {
    backgroundColor: '#3b82f6', borderRadius: 8, padding: 15, alignItems: 'center', marginTop: 8,
  },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  link: { color: '#3b82f6', textAlign: 'center', marginTop: 20 },
});
