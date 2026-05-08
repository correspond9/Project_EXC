import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import api from '../lib/api';

interface Notification {
  id: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  function loadNotifications() {
    setLoading(true);
    api
      .get('/api/notifications')
      .then((res) => setNotifications(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  async function markRead(id: string) {
    try {
      await api.put(`/api/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {}
  }

  async function markAllRead() {
    try {
      await api.put('/api/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#3b82f6" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>
          Alerts {unreadCount > 0 && <Text style={styles.badge}> {unreadCount}</Text>}
        </Text>
        {unreadCount > 0 && (
          <TouchableOpacity onPress={markAllRead} accessibilityLabel="Mark all notifications as read">
            <Text style={styles.markAll}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>

      {notifications.length === 0 ? (
        <Text style={styles.empty}>No notifications yet.</Text>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.card, !item.is_read && styles.cardUnread]}
              onPress={() => markRead(item.id)}
              accessibilityLabel={`Notification: ${item.message}`}
              accessibilityRole="button"
            >
              <View style={styles.row}>
                <View style={[styles.typeBadge, getTypeStyle(item.notification_type)]}>
                  <Text style={styles.typeText}>{item.notification_type}</Text>
                </View>
                <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</Text>
              </View>
              <Text style={[styles.message, !item.is_read && styles.messageUnread]}>
                {item.message}
              </Text>
            </TouchableOpacity>
          )}
          contentContainerStyle={{ paddingBottom: 24 }}
        />
      )}
    </View>
  );
}

function getTypeStyle(type: string) {
  if (type === 'FILL') return { backgroundColor: 'rgba(34,197,94,0.2)' };
  if (type === 'LIQUIDATION') return { backgroundColor: 'rgba(239,68,68,0.2)' };
  if (type === 'MARGIN_CALL') return { backgroundColor: 'rgba(234,179,8,0.2)' };
  return { backgroundColor: 'rgba(59,130,246,0.2)' };
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117' },
  center: { flex: 1, backgroundColor: '#0d1117', justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    margin: 16, marginTop: 52,
  },
  title: { fontSize: 22, fontWeight: '700', color: '#e6edf3' },
  badge: { color: '#ef4444', fontSize: 16 },
  markAll: { color: '#3b82f6', fontSize: 13 },
  empty: { color: '#8b949e', textAlign: 'center', marginTop: 60 },
  card: {
    marginHorizontal: 16, marginBottom: 8, backgroundColor: '#161b22',
    borderRadius: 10, padding: 14, borderWidth: 1, borderColor: '#21262d',
  },
  cardUnread: { borderColor: '#3b82f6' },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  typeBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  typeText: { fontSize: 10, fontWeight: '700', color: '#e6edf3' },
  date: { fontSize: 11, color: '#8b949e' },
  message: { fontSize: 13, color: '#8b949e', lineHeight: 18 },
  messageUnread: { color: '#e6edf3' },
});
