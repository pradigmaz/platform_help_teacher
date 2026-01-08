"use client";

import { Search, Filter } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ACTION_LABELS } from "../lib/audit-constants";

interface AuditFiltersProps {
  actionFilter: string;
  ipFilter: string;
  pathFilter: string;
  onActionChange: (value: string) => void;
  onIpChange: (value: string) => void;
  onPathChange: (value: string) => void;
  onSearch: () => void;
}

export function AuditFilters({
  actionFilter,
  ipFilter,
  pathFilter,
  onActionChange,
  onIpChange,
  onPathChange,
  onSearch,
}: AuditFiltersProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Фильтры
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-4">
          <Select value={actionFilter} onValueChange={onActionChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Тип действия" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все действия</SelectItem>
              {Object.entries(ACTION_LABELS).map(([key, { label }]) => (
                <SelectItem key={key} value={key}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Input
            placeholder="IP адрес"
            value={ipFilter}
            onChange={(e) => onIpChange(e.target.value)}
            className="w-[180px]"
          />
          
          <Input
            placeholder="Путь содержит..."
            value={pathFilter}
            onChange={(e) => onPathChange(e.target.value)}
            className="w-[200px]"
          />
          
          <Button onClick={onSearch}>
            <Search className="h-4 w-4 mr-2" />
            Поиск
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
