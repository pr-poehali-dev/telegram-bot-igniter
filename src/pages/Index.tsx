import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

interface Friend {
  id: string;
  username: string;
  streak: number;
  lastMessage: string;
  unread: boolean;
  restoresLeft: number;
}

const Index = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'friends' | 'profile'>('home');
  const [inviteUsername, setInviteUsername] = useState('');
  const [friends, setFriends] = useState<Friend[]>([
    { id: '1', username: 'alex_dev', streak: 12, lastMessage: '2 часа назад', unread: true, restoresLeft: 3 },
    { id: '2', username: 'maria_design', streak: 45, lastMessage: '5 минут назад', unread: false, restoresLeft: 2 },
    { id: '3', username: 'ivan_pro', streak: 7, lastMessage: '1 день назад', unread: true, restoresLeft: 3 },
  ]);

  const handleInvite = () => {
    if (!inviteUsername.trim()) {
      toast.error('Введите username друга');
      return;
    }
    
    const existing = friends.find(f => f.username.toLowerCase() === inviteUsername.toLowerCase());
    if (existing) {
      toast.error('Этот пользователь уже в списке');
      return;
    }

    toast.success(`Запрос отправлен @${inviteUsername}`);
    setInviteUsername('');
  };

  const totalStreak = friends.reduce((sum, f) => sum + f.streak, 0);
  const longestStreak = Math.max(...friends.map(f => f.streak), 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted">
      <div className="max-w-md mx-auto pb-20">
        <header className="pt-8 pb-6 px-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <span className="fire-glow">🔥</span> Огоньки
              </h1>
              <p className="text-sm text-muted-foreground mt-1">Поддерживай общение каждый день</p>
            </div>
            <Avatar className="h-12 w-12 border-2 border-primary">
              <AvatarFallback className="bg-primary text-primary-foreground font-semibold">
                Я
              </AvatarFallback>
            </Avatar>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Card className="p-4 bg-card/50 backdrop-blur border-primary/20">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xl">📊</span>
                <span className="text-sm text-muted-foreground">Всего дней</span>
              </div>
              <p className="text-2xl font-bold text-primary">{totalStreak}</p>
            </Card>

            <Card className="p-4 bg-card/50 backdrop-blur border-accent/20">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xl">🏆</span>
                <span className="text-sm text-muted-foreground">Рекорд</span>
              </div>
              <p className="text-2xl font-bold text-accent">{longestStreak}</p>
            </Card>
          </div>
        </header>

        {activeTab === 'home' && (
          <div className="px-6 space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xl font-semibold">Твои огоньки</h2>
              <Badge variant="secondary" className="gap-1">
                <Icon name="Flame" size={14} />
                {friends.filter(f => f.streak > 0).length} активных
              </Badge>
            </div>

            <ScrollArea className="h-[calc(100vh-380px)]">
              <div className="space-y-3 pr-4">
                {friends.map((friend) => (
                  <Card
                    key={friend.id}
                    className="p-4 hover:bg-card/80 transition-all cursor-pointer border-l-4 border-l-primary relative overflow-hidden group"
                    onClick={() => {
                      toast.info(`Открываем чат с @${friend.username}`);
                    }}
                  >
                    <div className="absolute top-2 right-2">
                      {friend.unread && (
                        <Badge variant="destructive" className="h-6 w-6 rounded-full p-0 flex items-center justify-center animate-pulse">
                          !
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-start gap-3">
                      <Avatar className="h-12 w-12 border-2 border-muted">
                        <AvatarFallback className="bg-muted text-foreground font-semibold">
                          {friend.username[0].toUpperCase()}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-semibold truncate">@{friend.username}</p>
                          {friend.streak >= 30 && <span className="text-lg">👑</span>}
                        </div>

                        <div className="flex items-center gap-2 mb-2">
                          <div className="flex items-center gap-1">
                            <span className={`text-xl ${friend.streak > 0 ? 'fire-pulse' : 'grayscale'}`}>
                              🔥
                            </span>
                            <span className="text-lg font-bold text-primary">{friend.streak}</span>
                            <span className="text-sm text-muted-foreground">дней</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Icon name="Clock" size={12} />
                            {friend.lastMessage}
                          </span>
                          <span className="flex items-center gap-1">
                            <Icon name="Shield" size={12} />
                            {friend.restoresLeft}/3 защит
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {activeTab === 'friends' && (
          <div className="px-6 space-y-4">
            <div>
              <h2 className="text-xl font-semibold mb-4">Пригласить друга</h2>
              
              <Card className="p-4 mb-6 bg-secondary/10 border-secondary/30">
                <div className="flex gap-2">
                  <Input
                    placeholder="username друга"
                    value={inviteUsername}
                    onChange={(e) => setInviteUsername(e.target.value)}
                    className="bg-background"
                    onKeyDown={(e) => e.key === 'Enter' && handleInvite()}
                  />
                  <Button onClick={handleInvite} className="shrink-0">
                    <Icon name="UserPlus" size={18} />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Введите @username друга из Telegram
                </p>
              </Card>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Входящие запросы</h3>
              <Card className="p-4 bg-accent/10 border-accent/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className="bg-accent text-accent-foreground">
                        N
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-semibold">@new_friend</p>
                      <p className="text-xs text-muted-foreground">Хочет начать огонёк</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => toast.error('Запрос отклонён')}>
                      <Icon name="X" size={16} />
                    </Button>
                    <Button size="sm" onClick={() => toast.success('Огонёк начат! 🔥')}>
                      <Icon name="Check" size={16} />
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="px-6 space-y-4">
            <Card className="p-6 text-center bg-gradient-to-br from-primary/20 to-accent/20 border-primary/30">
              <Avatar className="h-24 w-24 mx-auto mb-4 border-4 border-primary">
                <AvatarFallback className="bg-primary text-primary-foreground text-3xl font-bold">
                  Я
                </AvatarFallback>
              </Avatar>
              <h2 className="text-2xl font-bold mb-1">@your_username</h2>
              <p className="text-muted-foreground mb-4">Огненный воин 🔥</p>
              
              <div className="grid grid-cols-3 gap-4 mt-6">
                <div>
                  <p className="text-2xl font-bold text-primary">{friends.length}</p>
                  <p className="text-xs text-muted-foreground">Друзей</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-accent">{longestStreak}</p>
                  <p className="text-xs text-muted-foreground">Рекорд</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-secondary">{totalStreak}</p>
                  <p className="text-xs text-muted-foreground">Всего</p>
                </div>
              </div>
            </Card>

            <div>
              <h3 className="text-lg font-semibold mb-3">Достижения</h3>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { emoji: '🔥', name: 'Первый огонёк', unlocked: true },
                  { emoji: '⚡', name: '7 дней', unlocked: true },
                  { emoji: '💪', name: '30 дней', unlocked: true },
                  { emoji: '👑', name: '100 дней', unlocked: false },
                  { emoji: '🚀', name: '365 дней', unlocked: false },
                  { emoji: '💎', name: '5 друзей', unlocked: false },
                ].map((achievement, i) => (
                  <Card
                    key={i}
                    className={`p-3 text-center ${
                      achievement.unlocked ? 'bg-primary/10 border-primary/30' : 'bg-muted/20 opacity-50'
                    }`}
                  >
                    <div className={`text-3xl mb-1 ${achievement.unlocked ? '' : 'grayscale'}`}>
                      {achievement.emoji}
                    </div>
                    <p className="text-xs font-medium">{achievement.name}</p>
                  </Card>
                ))}
              </div>
            </div>

            <Card className="p-4">
              <Button variant="outline" className="w-full justify-start gap-2">
                <Icon name="Settings" size={18} />
                Настройки уведомлений
              </Button>
            </Card>
          </div>
        )}
      </div>

      <nav className="fixed bottom-0 left-0 right-0 bg-card/80 backdrop-blur-lg border-t border-border">
        <div className="max-w-md mx-auto px-6 py-3">
          <div className="flex justify-around items-center">
            <Button
              variant={activeTab === 'home' ? 'default' : 'ghost'}
              size="sm"
              className="flex-col h-auto py-2 gap-1"
              onClick={() => setActiveTab('home')}
            >
              <Icon name="Flame" size={20} />
              <span className="text-xs">Огоньки</span>
            </Button>
            
            <Button
              variant={activeTab === 'friends' ? 'default' : 'ghost'}
              size="sm"
              className="flex-col h-auto py-2 gap-1 relative"
              onClick={() => setActiveTab('friends')}
            >
              <Icon name="UserPlus" size={20} />
              <span className="text-xs">Друзья</span>
              <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                1
              </Badge>
            </Button>
            
            <Button
              variant={activeTab === 'profile' ? 'default' : 'ghost'}
              size="sm"
              className="flex-col h-auto py-2 gap-1"
              onClick={() => setActiveTab('profile')}
            >
              <Icon name="User" size={20} />
              <span className="text-xs">Профиль</span>
            </Button>
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Index;
